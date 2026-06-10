#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="pepadmet"
MINIFORGE_ROOT="/home/dongjukim/miniforge3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${WORK_DIR}/apply_estate_patch.log"
DRY_RUN=0
VERIFY=0

usage() {
    cat <<USAGE
Usage: bash scripts/apply_estate_patch.sh [--dry-run] [--verify]

Options:
  --dry-run   Print actions without modifying estate.py.
  --verify    Run pepADMET sample descriptor generation after patch check.
  -h, --help  Show this help.
USAGE
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            ;;
        --verify)
            VERIFY=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            fail "Unknown option: $1"
            ;;
    esac
    shift
done

mkdir -p "$(dirname "${LOG_FILE}")"
exec > >(tee -a "${LOG_FILE}") 2>&1

log "Starting PyBioMed estate.py patch check"
log "Log file: ${LOG_FILE}"

if [ "${DRY_RUN}" -eq 1 ]; then
    log "Mode: dry-run (no file changes)"
fi

command -v conda >/dev/null 2>&1 || fail "conda command not found"
[ -d "${MINIFORGE_ROOT}" ] || fail "Miniforge root not found: ${MINIFORGE_ROOT}"

env_matches="$(conda env list | grep -i "${ENV_NAME}" || true)"
[ -n "${env_matches}" ] || fail "No conda env matching '${ENV_NAME}' found in 'conda env list'"

env_path="$(
    printf '%s\n' "${env_matches}" |
        awk -v env_name="${ENV_NAME}" 'tolower($1) == env_name {print $NF}' |
        head -n 1
)"

[ -n "${env_path}" ] || fail "Could not identify exact conda env named '${ENV_NAME}' from: ${env_matches}"
[ -d "${env_path}" ] || fail "Detected env path does not exist: ${env_path}"

case "${env_path}" in
    "${MINIFORGE_ROOT}/envs/${ENV_NAME}"|"${MINIFORGE_ROOT}/envs/${ENV_NAME}/")
        ;;
    *)
        fail "Refusing unexpected '${ENV_NAME}' env path: ${env_path}"
        ;;
esac

log "Detected conda env: ${ENV_NAME} -> ${env_path}"

mapfile -t estate_candidates < <(
    find "${MINIFORGE_ROOT}" -name estate.py -path '*PyMolecule*' -print |
        awk -v env_path="${env_path}" 'index($0, env_path "/") == 1'
)

[ "${#estate_candidates[@]}" -gt 0 ] || fail "No estate.py found under ${env_path}"

valid_candidates=()
for candidate in "${estate_candidates[@]}"; do
    case "${candidate}" in
        "${env_path}"/lib/python*/site-packages/PyBioMed/PyMolecule/estate.py)
            valid_candidates+=("${candidate}")
            ;;
        *)
            log "Ignoring non-target estate.py candidate: ${candidate}"
            ;;
    esac
done

[ "${#valid_candidates[@]}" -eq 1 ] || fail "Expected exactly one safe estate.py target, found ${#valid_candidates[@]}"

estate_file="${valid_candidates[0]}"
[ -f "${estate_file}" ] || fail "Target is not a regular file: ${estate_file}"
[ -w "${estate_file}" ] || fail "Target is not writable: ${estate_file}"

log "Target estate.py: ${estate_file}"

if grep -q 'round(float(j), 3)' "${estate_file}"; then
    log "Patch already applied; no changes needed"
else
    grep -q 'round(j, 3)' "${estate_file}" || fail "Target pattern 'round(j, 3)' not found; refusing to edit"

    backup_file="${estate_file}.bak.$(date '+%Y%m%d_%H%M%S')"
    if [ "${DRY_RUN}" -eq 1 ]; then
        log "Would create backup: ${backup_file}"
        log "Would replace 'round(j, 3)' with 'round(float(j), 3)'"
    else
        cp -p "${estate_file}" "${backup_file}"
        log "Backup created: ${backup_file}"
        sed -i 's/round(j, 3)/round(float(j), 3)/g' "${estate_file}"
        grep -q 'round(float(j), 3)' "${estate_file}" || fail "Patch verification failed after sed replacement"
        log "Patch applied and verified"
    fi
fi

if [ "${VERIFY}" -eq 1 ]; then
    pepadmet_repo="${WORK_DIR}/pepADMET"
    [ -d "${pepadmet_repo}" ] || fail "--verify requested but pepADMET repo not found: ${pepadmet_repo}"
    [ -f "${pepadmet_repo}/calculate_descriptors.py" ] || fail "--verify requested but calculate_descriptors.py not found"

    if [ "${DRY_RUN}" -eq 1 ]; then
        log "Would run sample verification in ${pepadmet_repo}: conda run --no-capture-output -n ${ENV_NAME} python calculate_descriptors.py"
    else
        log "Running sample verification in ${pepadmet_repo}"
        (
            cd "${pepadmet_repo}"
            conda run --no-capture-output -n "${ENV_NAME}" python calculate_descriptors.py
            conda run --no-capture-output -n "${ENV_NAME}" python - <<'PY'
import pandas as pd

path = "data/example_feature_result.csv"
df = pd.read_csv(path)
error_count = int(df["Error"].notna().sum()) if "Error" in df.columns else 0
print("verification_csv:", path)
print("verification_shape:", df.shape)
print("verification_error_count:", error_count)
if error_count:
    raise SystemExit("sample verification produced descriptor errors")
PY
        )
        log "Sample verification completed"
    fi
fi

log "Done"
