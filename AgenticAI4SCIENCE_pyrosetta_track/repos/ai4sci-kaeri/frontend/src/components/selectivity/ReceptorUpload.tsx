import { useRef } from 'react'
import { Upload, CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import type { ReceptorStatus } from '../../hooks/useSelectivity'

interface Props { receptors: ReceptorStatus[]; onUpload: (t: string, f: File) => Promise<void>; onRefresh: () => Promise<void> }

export function ReceptorUpload({ receptors, onUpload, onRefresh }: Props) {
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({})
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--text-mute)]">Receptor Structures</h2>
        <button onClick={onRefresh} className="text-[10px] text-[var(--accent)] hover:text-[var(--accent)] flex items-center gap-1"><RefreshCw className="w-3 h-3" /> Refresh</button>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {receptors.map(r => (
          <div key={r.name} className={`rounded-lg border p-3 text-center ${r.loaded ? 'border-[var(--pos)]/30 bg-[var(--pos-soft)]' : 'border-[var(--border)] bg-[var(--bg-elev)]'}`}>
            {r.loaded ? <CheckCircle2 className="w-4 h-4 text-[var(--pos)] mx-auto" /> : <XCircle className="w-4 h-4 text-[var(--text-dim)] mx-auto" />}
            <p className="text-xs font-semibold text-[var(--text-mute)] mt-1">{r.name}</p>
            {r.pdb_id && <p className="text-[10px] text-[var(--text-dim)]">{r.pdb_id}</p>}
            {r.loaded ? <p className="text-[10px] text-[var(--pos)] mt-1">{r.size_kb ? `${r.size_kb} KB` : 'Loaded'}</p> : (
              <><input ref={el => { fileRefs.current[r.name] = el }} type="file" accept=".pdb,.cif" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) onUpload(r.name, f) }} />
              <button onClick={() => fileRefs.current[r.name]?.click()} className="mt-1 text-[10px] text-[var(--accent)] hover:text-[var(--accent)] flex items-center gap-1 mx-auto"><Upload className="w-3 h-3" /> Upload</button></>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
