import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { Beaker, ChevronRight, Clock3, FileText, Loader2, Truck } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Sequence } from '../components/dashboard/Sequence'
import { useTransitionWetlabOrder, useWetlabOrder, useWetlabOrders, type WetlabStage } from '../hooks/dashboard'

const STAGES: WetlabStage[] = ['draft', 'submitted', 'approved', 'shipped', 'returned']

export function WetlabOrderPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const ordersQuery = useWetlabOrders()
  const resolvedId = id ?? ordersQuery.data?.orders[0]?.id
  const orderQuery = useWetlabOrder(resolvedId)
  const transition = useTransitionWetlabOrder()

  useEffect(() => {
    if (!id && resolvedId) {
      navigate(`/wetlab/orders/${resolvedId}`, { replace: true })
    }
  }, [id, navigate, resolvedId])

  const orders = ordersQuery.data?.orders ?? []
  const order = orderQuery.data
  const activeStageIndex = order ? STAGES.indexOf(order.stage) : -1
  const nextStage = activeStageIndex >= 0 && activeStageIndex < STAGES.length - 1 ? STAGES[activeStageIndex + 1] : null

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-rose-500/30 bg-rose-500/15">
          <Beaker className="h-4 w-4 text-[var(--neg)]" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-text-base">Wetlab Order</h1>
          <p className="text-[10px] text-text-mute">Procurement and assay planning for in-vitro SSTR binding validation</p>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
        <section className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
          <div className="border-b border-border-base px-4 py-3">
            <h2 className="text-sm font-semibold text-text-base">Orders</h2>
            <p className="text-[10px] text-text-mute">{orders.length} available orders</p>
          </div>

          {ordersQuery.isLoading ? (
            <div className="flex items-center justify-center px-4 py-8 text-xs text-text-mute">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading orders…
            </div>
          ) : orders.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs text-text-mute">No wetlab orders found.</div>
          ) : (
            <div className="divide-y divide-border-base">
              {orders.map((item) => {
                const active = item.id === resolvedId
                return (
                  <Link
                    key={item.id}
                    to={`/wetlab/orders/${item.id}`}
                    className={`block px-4 py-3 transition-colors ${active ? 'bg-rose-500/10' : 'hover:bg-bg-elev/20'}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-text-base">{item.id}</span>
                      <StagePill stage={item.stage} />
                    </div>
                    <div className="mt-1 text-[11px] text-text-mute">{item.candidate_id}</div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-text-dim">
                      <span>{formatCurrency(item.total_krw)}</span>
                      <span>{item.lead_weeks} weeks</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </section>

        <section className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
          {!order ? (
            <div className="px-4 py-12 text-center text-xs text-text-mute">
              {orderQuery.isLoading ? 'Loading order detail…' : 'Select an order to inspect details.'}
            </div>
          ) : (
            <>
              <div className="border-b border-border-base px-4 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-semibold text-text-base">{order.id}</span>
                  <StagePill stage={order.stage} />
                  <span className="rounded border border-border-base bg-bg px-2 py-0.5 font-mono text-[10px] text-text-mute">{order.candidate_id}</span>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] text-text-mute">
                  <span className="inline-flex items-center gap-1"><Clock3 className="h-3 w-3" /> {order.lead_weeks} week timeline</span>
                  <span className="inline-flex items-center gap-1"><Truck className="h-3 w-3" /> {formatCurrency(order.total_krw)}</span>
                  <span className="inline-flex items-center gap-1"><FileText className="h-3 w-3" /> {order.requested_by}</span>
                </div>
                <div className="mt-3">
                  <Sequence seq={order.candidate_seq} big />
                </div>
              </div>

              <div className="border-b border-border-base px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  {STAGES.map((stage, index) => {
                    const reached = index <= activeStageIndex
                    const clickable = nextStage === stage && !transition.isPending
                    return (
                      <div key={stage} className="flex items-center gap-2">
                        <button
                          type="button"
                          disabled={!clickable}
                          onClick={() => transition.mutate({ orderId: order.id, to_stage: stage })}
                          className={`rounded-full border px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] ${
                            clickable
                              ? 'border-rose-400/50 bg-rose-500/15 text-rose-200 hover:bg-rose-500/25'
                              : reached
                                ? 'border-[var(--pos)]/30 bg-[var(--pos-soft)] text-[var(--pos)]'
                                : 'border-border-base bg-bg text-text-dim'
                          }`}
                        >
                          {stage}
                        </button>
                        {index < STAGES.length - 1 ? <ChevronRight className="h-3 w-3 text-text-dim" /> : null}
                      </div>
                    )
                  })}
                </div>
                {transition.isError ? (
                  <p className="mt-2 text-xs text-[var(--neg)]">Stage transition failed.</p>
                ) : nextStage ? (
                  <p className="mt-2 text-[10px] text-text-dim">Only the next stage is mutable. Current next step: `{nextStage}`.</p>
                ) : (
                  <p className="mt-2 text-[10px] text-text-dim">Order has reached the terminal returned state.</p>
                )}
              </div>

              <div className="grid gap-4 px-4 py-4 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div className="space-y-4">
                  <Panel title="Hypothesis">
                    <HypothesisBlock label="H1" text={order.hypothesis.h1} tone="emerald" />
                    <HypothesisBlock label="H0" text={order.hypothesis.h0} tone="slate" />
                  </Panel>

                  <Panel title="Predicted Ki">
                    <div className="overflow-auto">
                      <table className="w-full text-xs">
                        <thead className="border-b border-border-base text-left text-[10px] uppercase tracking-[0.14em] text-text-dim">
                          <tr>
                            <th className="px-3 py-2">Receptor</th>
                            <th className="px-3 py-2 text-right">iPTM</th>
                            <th className="px-3 py-2 text-right">SST-14 Ki</th>
                            <th className="px-3 py-2 text-right">Prediction</th>
                          </tr>
                        </thead>
                        <tbody>
                          {order.predicted_ki.map((item) => (
                            <tr key={item.receptor} className={`border-b border-border-base/20 ${item.target ? 'bg-[var(--pos-soft)]' : ''}`}>
                              <td className="px-3 py-2 font-mono text-text-base">{item.target ? '★ ' : ''}{item.receptor}</td>
                              <td className="px-3 py-2 text-right font-mono text-text-mute">{item.iptm.toFixed(3)}</td>
                              <td className="px-3 py-2 text-right font-mono text-text-mute">{item.sst14_ki_nm ?? '—'} nM</td>
                              <td className={`px-3 py-2 text-right font-mono ${item.target ? 'text-[var(--pos)]' : 'text-text-mute'}`}>{item.predicted_ki}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Panel>

                  <Panel title="Procurement">
                    <div className="overflow-auto">
                      <table className="w-full text-xs">
                        <thead className="border-b border-border-base text-left text-[10px] uppercase tracking-[0.14em] text-text-dim">
                          <tr>
                            <th className="px-3 py-2">Item</th>
                            <th className="px-3 py-2">Vendor</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-right">Unit</th>
                            <th className="px-3 py-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {order.reagents.map((reagent) => (
                            <tr key={reagent.name} className="border-b border-border-base/20">
                              <td className="px-3 py-2">
                                <div className="font-mono text-text-base">{reagent.name}</div>
                                <div className="text-[11px] text-text-dim">{reagent.spec}</div>
                              </td>
                              <td className="px-3 py-2 font-mono text-text-mute">{reagent.vendor}</td>
                              <td className="px-3 py-2 text-right font-mono text-text-mute">{reagent.qty}</td>
                              <td className="px-3 py-2 text-right font-mono text-text-mute">{formatCurrency(reagent.unit_price_krw)}</td>
                              <td className="px-3 py-2 text-right font-mono text-text-base">{formatCurrency(reagent.unit_price_krw * reagent.qty)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Panel>
                </div>

                <div className="space-y-4">
                  <Panel title="Protocol">
                    <Definition label="Format" value={order.protocol.format} />
                    <Definition label="Tracer" value={order.protocol.tracer} />
                    <Definition label="Membrane" value={order.protocol.membrane} />
                    <Definition label="Range" value={order.protocol.concentration_range} />
                    <Definition label="Replicates" value={order.protocol.replicates} />
                    <Definition label="Negative" value={order.protocol.negative_control} />
                    <Definition label="Readout" value={order.protocol.readout} />
                    <Definition label="Analysis" value={order.protocol.analysis} />
                  </Panel>

                  <Panel title="Acceptance">
                    <div className="space-y-2">
                      {order.acceptance_criteria.map((criterion) => (
                        <div key={criterion.criterion} className="rounded-lg border border-border-base bg-bg px-3 py-2 text-xs text-text-mute">
                          {criterion.criterion}
                        </div>
                      ))}
                    </div>
                  </Panel>

                  <Panel title="Timeline">
                    <div className="space-y-2">
                      {order.timeline.map((entry) => (
                        <div key={`${entry.week}-${entry.task}`} className="grid grid-cols-[52px_minmax(0,1fr)_60px] gap-2 border-b border-border-base/20 pb-2 text-xs">
                          <span className="font-mono text-text-dim">{entry.week}</span>
                          <span className="text-text-mute">{entry.task}</span>
                          <span className="font-mono text-text-dim">{entry.actor}</span>
                        </div>
                      ))}
                    </div>
                  </Panel>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-border-base bg-bg">
      <div className="border-b border-border-base px-4 py-3 text-sm font-semibold text-text-base">{title}</div>
      <div className="space-y-3 px-4 py-4">{children}</div>
    </section>
  )
}

function HypothesisBlock({ label, text, tone }: { label: string; text: string; tone: 'emerald' | 'slate' }) {
  const toneClass = tone === 'emerald'
    ? 'border-[var(--pos)]/30 bg-[var(--pos-soft)] text-emerald-100'
    : 'border-border-base bg-bg-elev text-text-mute'
  return (
    <div className={`rounded-lg border px-3 py-3 text-xs leading-5 ${toneClass}`}>
      <div className="mb-1 font-mono font-semibold">{label}</div>
      <div>{text}</div>
    </div>
  )
}

function Definition({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-border-base/20 pb-2">
      <div className="text-[10px] uppercase tracking-[0.14em] text-text-dim">{label}</div>
      <div className="mt-1 text-xs text-text-mute">{value}</div>
    </div>
  )
}

function StagePill({ stage }: { stage: WetlabStage }) {
  const styles: Record<WetlabStage, string> = {
    draft: 'border-border-base bg-bg text-text-mute',
    submitted: 'border-[var(--accent)]/30 bg-[var(--accent-soft)] text-[var(--accent)]',
    approved: 'border-[var(--pos)]/30 bg-[var(--pos-soft)] text-[var(--pos)]',
    shipped: 'border-[var(--warn)]/30 bg-[var(--warn-soft)] text-[var(--warn)]',
    returned: 'border-[var(--violet)]/30 bg-[var(--violet-soft)] text-[var(--violet)]',
  }
  return (
    <span className={`rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase ${styles[stage]}`}>
      {stage}
    </span>
  )
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 }).format(value)
}
