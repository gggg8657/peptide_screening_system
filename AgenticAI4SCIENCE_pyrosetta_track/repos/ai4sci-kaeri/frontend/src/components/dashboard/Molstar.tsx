/**
 * Molstar — 실제 npm Mol* 패키지로 PDB 구조 로딩.
 *
 * 위치: src/components/Molstar.tsx
 *
 * 의존:
 *   npm install molstar
 *
 * 기본: RCSB 의 7XNA (SSTR2 holo) 로드.
 * pdbUrl prop 으로 backend 의 docked pose PDB (e.g. /api/static/{run_id}/05_docking/pose_a_{candId}.pdb) 직접 지정 가능.
 */

import { useEffect, useRef } from 'react';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui';
import { renderReact18 } from 'molstar/lib/mol-plugin-ui/react18';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import type { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';

interface Props {
  pdbId?: string;
  pdbUrl?: string;
  height?: number | string;
  className?: string;
}

export function Molstar({ pdbId = '7XNA', pdbUrl, height = 320, className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const pluginRef = useRef<PluginUIContext | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!ref.current) return;

    (async () => {
      try {
        const spec = DefaultPluginUISpec();
        spec.components = {
          ...spec.components,
          remoteState: 'none',
          viewport: {
            ...spec.components?.viewport,
            controls: undefined,
          },
          sequenceViewer: {
            ...spec.components?.sequenceViewer,
            view: undefined,
          },
          hideTaskOverlay: true,
        };

        const plugin = await createPluginUI({
          target: ref.current!,
          render: renderReact18,
          spec,
        });
        if (cancelled) {
          plugin.dispose();
          return;
        }
        pluginRef.current = plugin;

        const url = pdbUrl ?? `https://files.rcsb.org/download/${pdbId}.pdb`;
        const isCif = url.endsWith('.cif');
        const data = await plugin.builders.data.download(
          { url, isBinary: false },
          { state: { isGhost: false } },
        );
        const trajectory = await plugin.builders.structure.parseTrajectory(
          data,
          isCif ? 'mmcif' : 'pdb',
        );
        await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
      } catch (e) {
        console.error('Molstar load failed:', e);
      }
    })();

    return () => {
      cancelled = true;
      if (pluginRef.current) {
        pluginRef.current.dispose();
        pluginRef.current = null;
      }
      // cleanup: pdbUrl 변경 시 이전 Mol* DOM 잔여물 제거
      if (ref.current) {
        ref.current.innerHTML = '';
      }
    };
  }, [pdbId, pdbUrl]);

  return (
    <div
      ref={ref}
      className={
        'relative w-full rounded border border-border-base bg-bg-sunk overflow-hidden ' +
        (className ?? '')
      }
      style={{ height }}
    />
  );
}
