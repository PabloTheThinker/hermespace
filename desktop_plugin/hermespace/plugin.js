/**
 * Hermespace Desktop plugin — dual surface that actually loads.
 *
 * Contract (Hermes Desktop current):
 * - Badge variants: default | muted | warn | destructive | outline (NOT secondary)
 * - StatusDot tones: good | muted | warn | bad (NOT success/warning/danger)
 * - Palette: run INSIDE data
 * - Folder name == plugin.id == hermespace
 * - Install as REAL file under $HERMES_HOME/desktop-plugins/hermespace/plugin.js
 *   (symlink to another tree breaks some Desktop/remote read paths)
 *
 * Surfaces:
 *  1) panes tile — immediate, dockable (like ilo-ops; users find this)
 *  2) full page /hermespace + sidebar.nav (first-class)
 *  3) status chip + palette → navigate /hermespace
 */
import {
  Badge,
  Button,
  EmptyState,
  PALETTE_AREA,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  StatusDot,
  Tip,
  cn,
  haptic,
  host,
  useValue
} from '@hermes/plugin-sdk'
import { jsx, jsxs, Fragment } from 'react/jsx-runtime'
import { useCallback, useEffect, useState } from 'react'

const PLUGIN_ID = 'hermespace'
const ROUTE_PATH = '/hermespace'
const DEFAULT_SOCKET = 'http://127.0.0.1:8764'
const STORAGE_SOCKET = 'socketUrl'

function toneOnline(on, n) {
  if (!on) return 'bad'
  if (n > 0) return 'warn'
  return 'good'
}

function toneGateway(state) {
  if (state === 'open' || state === 'connected') return 'good'
  if (state === 'connecting') return 'warn'
  if (!state || state === 'idle') return 'muted'
  return 'bad'
}

function candidatesFrom(base) {
  const list = []
  const push = u => {
    try {
      const origin = new URL(u).origin
      if (!list.includes(origin)) list.push(origin)
    } catch {
      /* skip */
    }
  }
  if (base) push(base)
  push(DEFAULT_SOCKET)
  push('http://localhost:8764')
  return list
}

async function probeSocket(origin, timeoutMs) {
  const ms = timeoutMs || 2500
  const ctrl = new AbortController()
  const t = setTimeout(function () {
    ctrl.abort()
  }, ms)
  try {
    const r = await fetch(origin + '/api/snapshot', { signal: ctrl.signal })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const snap = await r.json()
    return { ok: true, origin: origin, snap: snap }
  } catch (e) {
    return { ok: false, origin: origin, error: (e && e.message) || String(e) }
  } finally {
    clearTimeout(t)
  }
}

async function connectSocket(preferred) {
  const tried = []
  const cands = candidatesFrom(preferred)
  for (let i = 0; i < cands.length; i++) {
    const origin = cands[i]
    tried.push(origin)
    const res = await probeSocket(origin, 2500)
    if (res.ok) {
      res.tried = tried
      return res
    }
  }
  return {
    ok: false,
    origin: preferred || DEFAULT_SOCKET,
    error: 'No Hermespace socket reachable',
    tried: tried
  }
}

async function api(origin, path, opts) {
  const r = await fetch(
    origin + path,
    Object.assign({}, opts || {}, {
      headers: Object.assign({ 'Content-Type': 'application/json' }, (opts && opts.headers) || {})
    })
  )
  const data = await r.json().catch(function () {
    return {}
  })
  if (!r.ok) throw new Error(data.reason || data.error || 'HTTP ' + r.status)
  return data
}

function readStoredSocket() {
  try {
    return localStorage.getItem('hermespace:' + STORAGE_SOCKET) || DEFAULT_SOCKET
  } catch (e) {
    return DEFAULT_SOCKET
  }
}

function writeStoredSocket(url) {
  try {
    localStorage.setItem('hermespace:' + STORAGE_SOCKET, url)
  } catch (e) {
    /* ignore */
  }
}

function Row(props) {
  return jsxs('div', {
    className: 'flex items-start justify-between gap-2 text-[0.75rem] leading-snug',
    children: [
      jsx('span', { className: 'shrink-0 text-(--ui-text-tertiary)', children: props.label }),
      jsx('span', {
        className: 'min-w-0 text-right break-all text-(--ui-text-secondary)',
        children: props.value == null || props.value === '' ? '—' : String(props.value)
      })
    ]
  })
}

function Section(props) {
  return jsxs('section', {
    className: 'flex flex-col gap-2 rounded-lg border border-(--ui-border) p-2.5',
    children: [
      jsxs('div', {
        className: 'flex items-center justify-between gap-2',
        children: [
          jsx('div', {
            className:
              'text-[0.65rem] font-semibold uppercase tracking-wide text-(--ui-text-quaternary)',
            children: props.title
          }),
          props.action || null
        ]
      }),
      props.children
    ]
  })
}

/** Shared body used by pane + full page */
function HermespaceBody(props) {
  const compact = !!props.compact
  const gateway = useValue(host.state.gateway)
  const model = useValue(host.state.model)

  const [socketUrl, setSocketUrl] = useState(readStoredSocket)
  const [draftUrl, setDraftUrl] = useState(socketUrl)
  const [conn, setConn] = useState({ status: 'idle' })
  const [snap, setSnap] = useState(null)
  const [pending, setPending] = useState([])
  const [pulse, setPulse] = useState(null)
  const [controls, setControls] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [lastTried, setLastTried] = useState([])

  const saveSocket = useCallback(function (url) {
    const u = String(url || '')
      .trim()
      .replace(/\/$/, '') || DEFAULT_SOCKET
    setSocketUrl(u)
    setDraftUrl(u)
    writeStoredSocket(u)
    return u
  }, [])

  const refresh = useCallback(
    async function () {
      setBusy(true)
      setErr(null)
      try {
        const hit = await connectSocket(socketUrl)
        setLastTried(hit.tried || [])
        if (!hit.ok) {
          setConn({ status: 'offline', origin: hit.origin })
          setSnap(null)
          setPending([])
          setPulse(null)
          setControls(null)
          setErr(
            'Socket offline. On agent host run:\nPYTHONPATH=src ./scripts/hs view --serve --port 8764\nRemote Desktop: tunnel 8764 with 9119.'
          )
          return
        }
        if (hit.origin !== socketUrl) saveSocket(hit.origin)
        const s = await api(hit.origin, '/api/snapshot')
        let p = { pending: [] }
        let pu = null
        try {
          p = await api(hit.origin, '/api/pending')
        } catch (e1) {
          /* older serve */
        }
        try {
          pu = await api(hit.origin, '/api/pulse')
        } catch (e2) {
          /* optional */
        }
        let ctl = null
        try {
          ctl = await api(hit.origin, '/api/controls')
        } catch (e3) {
          /* optional */
        }
        setConn({ status: 'online', origin: hit.origin })
        setSnap(s)
        setPending(p.pending || [])
        setPulse(pu)
        setControls(ctl)
      } catch (e) {
        setConn({ status: 'offline' })
        setErr((e && e.message) || String(e))
      } finally {
        setBusy(false)
      }
    },
    [socketUrl, saveSocket]
  )

  useEffect(
    function () {
      refresh()
      const t = setInterval(refresh, 8000)
      return function () {
        clearInterval(t)
      }
    },
    [refresh]
  )

  const act = async function (kind, id) {
    if (!conn.origin) return
    haptic('tap')
    try {
      await api(conn.origin, '/api/' + kind, {
        method: 'POST',
        body: JSON.stringify({ id: id })
      })
      host.notify({ kind: 'info', message: kind + ' · ' + id })
      await refresh()
    } catch (e) {
      host.notify({ kind: 'error', message: (e && e.message) || String(e) })
    }
  }

  const runPulseTick = async function () {
    if (!conn.origin) return
    haptic('tap')
    try {
      const out = await api(conn.origin, '/api/pulse/tick', { method: 'POST', body: '{}' })
      host.notify({
        kind: 'info',
        message: 'pulse · ran ' + (out.ran != null ? out.ran : '?') + ' skip ' + (out.skipped != null ? out.skipped : '?')
      })
      await refresh()
    } catch (e) {
      host.notify({ kind: 'error', message: (e && e.message) || String(e) })
    }
  }

  const desk = (snap && snap.desk) || {}
  const lens = (snap && snap.lens) || {}
  const bound = (snap && snap.boundary) || {}
  const missions = (snap && snap.missions) || []
  const pulseJobs = (pulse && pulse.jobs) || []
  const online = conn.status === 'online'
  const shell = compact
    ? 'flex h-full flex-col gap-2 overflow-auto p-2.5 text-sm'
    : 'flex h-full flex-col gap-3 overflow-auto p-4 md:p-6 text-sm'


  const toggleFlag = async function (flag, enabled) {
    if (!conn.origin) return
    haptic('tap')
    try {
      var body = { agent_id: 'default', flags: {} }
      body.flags[flag] = enabled
      await api(conn.origin, '/api/controls', { method: 'POST', body: JSON.stringify(body) })
      host.notify({ kind: 'info', message: flag + ' → ' + (enabled ? 'on' : 'off') })
      await refresh()
    } catch (e) {
      host.notify({ kind: 'error', message: (e && e.message) || String(e) })
    }
  }

  const toggleJob = async function (id, enabled) {
    if (!conn.origin) return
    haptic('tap')
    try {
      await api(conn.origin, '/api/controls', {
        method: 'POST',
        body: JSON.stringify({ agent_id: 'default', job_id: id, enabled: enabled })
      })
      host.notify({ kind: 'info', message: 'job ' + id + ' → ' + (enabled ? 'on' : 'off') })
      await refresh()
    } catch (e) {
      host.notify({ kind: 'error', message: (e && e.message) || String(e) })
    }
  }

  return jsxs('div', {
    className: shell,
    children: [
      jsxs('div', {
        className: 'flex items-center justify-between gap-2',
        children: [
          jsxs('div', {
            className: 'flex items-center gap-2 min-w-0',
            children: [
              jsx('div', { className: 'font-semibold truncate', children: 'Hermespace' }),
              jsx(Badge, {
                variant: online ? 'default' : 'warn',
                children: online ? 'live' : 'off'
              }),
              jsx(StatusDot, { tone: toneOnline(online, pending.length), className: 'scale-90' })
            ]
          }),
          jsxs('div', {
            className: 'flex gap-1 shrink-0',
            children: [
              jsx(Button, {
                size: 'sm',
                variant: 'secondary',
                disabled: busy,
                onClick: function () {
                  haptic('tap')
                  refresh()
                },
                children: busy ? '…' : 'Refresh'
              }),
              !compact
                ? null
                : jsx(Button, {
                    size: 'sm',
                    variant: 'ghost',
                    onClick: function () {
                      haptic('tap')
                      host.navigate(ROUTE_PATH)
                    },
                    children: 'Page'
                  })
            ]
          })
        ]
      }),

      jsxs(Section, {
        title: 'Socket',
        children: [
          jsxs('div', {
            className: 'flex gap-1',
            children: [
              jsx('input', {
                value: draftUrl,
                onChange: function (e) {
                  setDraftUrl(e.target.value)
                },
                className:
                  'min-w-0 flex-1 rounded border border-(--ui-border) bg-(--ui-bg) px-1.5 py-1 font-mono text-[0.7rem]',
                placeholder: DEFAULT_SOCKET
              }),
              jsx(Button, {
                size: 'sm',
                onClick: function () {
                  haptic('tap')
                  saveSocket(draftUrl)
                  setTimeout(refresh, 0)
                },
                children: 'Set'
              })
            ]
          }),
          jsx(Row, { label: 'active', value: conn.origin || '—' }),
          jsx(Row, {
            label: 'gateway',
            value: (gateway || '—') + (model ? ' · ' + model : '')
          }),
          !online
            ? jsx('pre', {
                className: 'whitespace-pre-wrap font-mono text-[0.65rem] text-(--ui-text-tertiary)',
                children:
                  'hs view --serve --port 8764\n# tunnel 8764 if Desktop remote\n' +
                  (lastTried && lastTried.length ? 'probed: ' + lastTried.join(' ') : '')
              })
            : null,
          err
            ? jsx('div', {
                className: 'text-[0.7rem] text-amber-500 whitespace-pre-wrap',
                children: err
              })
            : null
        ]
      }),

      online
        ? jsxs(Fragment, {
            children: [
              jsxs(Section, {
                title: 'Controls',
                children: [
                  jsxs('div', {
                    className: 'flex flex-col gap-1.5 text-[0.75rem]',
                    children: [
                      ['autonomy', 'Autonomy'],
                      ['pulse_runtime', 'Pulse runtime'],
                      ['auto_dream', 'Auto dream'],
                      ['auto_order', 'Auto order']
                    ].map(function (pair) {
                      var key = pair[0]
                      var label = pair[1]
                      var on = !!(controls && controls.flags && controls.flags[key])
                      return jsxs(
                        'div',
                        {
                          className: 'flex items-center justify-between gap-2',
                          children: [
                            jsx('span', { children: label }),
                            jsx(Button, {
                              size: 'sm',
                              variant: on ? 'default' : 'secondary',
                              onClick: function () {
                                toggleFlag(key, !on)
                              },
                              children: on ? 'On' : 'Off'
                            })
                          ]
                        },
                        key
                      )
                    })
                  }),
                  jsx('div', {
                    className: 'text-[0.65rem] text-(--ui-text-tertiary)',
                    children:
                      'effective autonomy: ' +
                      (controls && controls.autonomy_effective ? 'on' : 'off')
                  }),
                  !compact && controls && controls.pulse_jobs
                    ? jsxs('div', {
                        className: 'flex flex-col gap-1 mt-2',
                        children: (controls.pulse_jobs || []).map(function (j) {
                          return jsxs(
                            'div',
                            {
                              className: 'flex justify-between gap-2 items-center',
                              children: [
                                jsx('span', {
                                  className: 'truncate',
                                  children: j.name || j.id
                                }),
                                jsx(Button, {
                                  size: 'sm',
                                  variant: j.enabled ? 'default' : 'secondary',
                                  onClick: function () {
                                    toggleJob(j.id, !j.enabled)
                                  },
                                  children: j.enabled ? 'On' : 'Off'
                                })
                              ]
                            },
                            j.id
                          )
                        })
                      })
                    : null
                ]
              }),

              jsxs(Section, {
                title: 'Desk',
                children: [
                  jsx(Row, { label: 'goal', value: desk.goal }),
                  jsx(Row, { label: 'decision', value: desk.decision }),
                  jsx(Row, {
                    label: 'load',
                    value: ((desk.load && desk.load.level) || '—') + ' / ' + (desk.executive || '—')
                  }),
                  jsx(Row, {
                    label: 'lens',
                    value: lens.title || lens.name || '—'
                  }),
                  jsx(Row, {
                    label: 'writes',
                    value: bound.project_write_default || 'deny'
                  }),
                  jsx(Row, { label: 'report', value: desk.say })
                ]
              }),

              jsxs(Section, {
                title: 'Access',
                action: jsx(Badge, {
                  variant: pending.length ? 'warn' : 'outline',
                  children: String(pending.length)
                }),
                children: [
                  pending.length === 0
                    ? jsx('div', {
                        className: 'text-[0.75rem] text-(--ui-text-tertiary)',
                        children: 'None — pocket sealed'
                      })
                    : pending.map(function (r) {
                        return jsxs(
                          'div',
                          {
                            className: 'rounded border border-(--ui-border) p-2 flex flex-col gap-1',
                            children: [
                              jsx('div', {
                                className: 'font-mono text-[0.7rem] break-all',
                                children: r.path
                              }),
                              jsx('div', {
                                className: 'text-[0.65rem] text-(--ui-text-tertiary)',
                                children: (r.reason || '') + ' · ' + r.id
                              }),
                              jsxs('div', {
                                className: 'flex gap-1',
                                children: [
                                  jsx(Button, {
                                    size: 'sm',
                                    onClick: function () {
                                      act('approve', r.id)
                                    },
                                    children: 'Approve'
                                  }),
                                  jsx(Button, {
                                    size: 'sm',
                                    variant: 'ghost',
                                    onClick: function () {
                                      act('deny', r.id)
                                    },
                                    children: 'Deny'
                                  })
                                ]
                              })
                            ]
                          },
                          r.id
                        )
                      })
                ]
              }),

              !compact
                ? jsxs(Section, {
                    title: 'Missions',
                    children: [
                      missions.length === 0
                        ? jsx('div', {
                            className: 'text-[0.75rem] text-(--ui-text-tertiary)',
                            children: 'No missions'
                          })
                        : missions.slice(0, 10).map(function (m) {
                            return jsx(
                              'div',
                              {
                                className: 'text-[0.72rem]',
                                children:
                                  '[' +
                                  (m.status || '?') +
                                  '] ' +
                                  (m.title || m.id)
                              },
                              m.id || m.title
                            )
                          })
                    ]
                  })
                : null,

              jsxs(Section, {
                title: 'Pulse',
                action: jsxs('div', {
                  className: 'flex gap-1 items-center',
                  children: [
                    jsx(Badge, {
                      variant: 'outline',
                      children: String(pulseJobs.length)
                    }),
                    jsx(Button, {
                      size: 'sm',
                      variant: 'secondary',
                      onClick: runPulseTick,
                      children: 'Tick'
                    })
                  ]
                }),
                children: [
                  pulseJobs.length === 0
                    ? jsx('div', {
                        className: 'text-[0.75rem] text-(--ui-text-tertiary)',
                        children: 'No /api/pulse yet — restart hs view --serve'
                      })
                    : pulseJobs.slice(0, compact ? 5 : 20).map(function (j) {
                        return jsxs(
                          'div',
                          {
                            className:
                              'flex justify-between gap-2 text-[0.7rem] border-b border-(--ui-border)/50 py-1 last:border-0',
                            children: [
                              jsx('span', {
                                className: 'truncate',
                                children: j.name || j.id
                              }),
                              jsx(Badge, {
                                variant: j.due && j.conditions_ok ? 'warn' : 'outline',
                                children: !j.enabled
                                  ? 'off'
                                  : j.due && j.conditions_ok
                                    ? 'due'
                                    : j.due_reason || 'ok'
                              })
                            ]
                          },
                          j.id
                        )
                      })
                ]
              })
            ]
          })
        : jsx(EmptyState, {
            title: 'Socket offline',
            description: 'Start hs view --serve on the agent host, tunnel 8764 if needed, Refresh.'
          })
    ]
  })
}

function HermespacePage() {
  return jsx(HermespaceBody, { compact: false })
}

function HermespacePane() {
  return jsx(HermespaceBody, { compact: true })
}

function Chip() {
  const [n, setN] = useState(0)
  const [on, setOn] = useState(false)
  useEffect(function () {
    let dead = false
    async function tick() {
      try {
        const hit = await connectSocket(readStoredSocket())
        if (dead) return
        if (!hit.ok) {
          setOn(false)
          setN(0)
          return
        }
        setOn(true)
        try {
          const p = await api(hit.origin, '/api/pending')
          if (!dead) setN((p.pending || []).length)
        } catch (e) {
          if (!dead) setN(0)
        }
      } catch (e2) {
        if (!dead) {
          setOn(false)
          setN(0)
        }
      }
    }
    tick()
    const t = setInterval(tick, 10000)
    return function () {
      dead = true
      clearInterval(t)
    }
  }, [])

  return jsx(Tip, {
    label: on ? (n ? n + ' access request(s)' : 'Hermespace live') : 'Hermespace offline',
    children: jsx('button', {
      type: 'button',
      className: cn(
        'inline-flex h-full items-center gap-1 px-1.5 text-[0.6875rem] transition-colors',
        'text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground'
      ),
      onClick: function () {
        haptic('tap')
        host.navigate(ROUTE_PATH)
      },
      children: [jsx(StatusDot, { tone: toneOnline(on, n), className: 'scale-75' }), n ? 'hs·' + n : 'hs']
    })
  })
}

export default {
  id: PLUGIN_ID,
  name: 'Hermespace',
  defaultEnabled: true,
  register: function (ctx) {
    // 1) Dockable pane — same class as working ilo-ops (always visible if plugins load)
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'hermespace',
      data: { placement: 'right', width: '300px', minWidth: '240px' },
      render: function () {
        return jsx(HermespacePane, {})
      }
    })

    // 2) Full page (sidebar opens via openRouteTile → this route)
    ctx.register({
      id: 'page',
      area: ROUTES_AREA,
      title: 'Hermespace',
      data: { path: ROUTE_PATH },
      render: function () {
        return jsx(HermespacePage, {})
      }
    })

    // 3) Sidebar nav row
    ctx.register({
      id: 'nav',
      area: SIDEBAR_NAV_AREA,
      order: 45,
      data: {
        codicon: 'globe',
        label: 'Hermespace',
        path: ROUTE_PATH
      }
    })

    // 4) Status chip
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 118,
      render: function () {
        return jsx(Chip, {})
      }
    })

    // 5) Palette
    ctx.register({
      id: 'cmd-open',
      area: PALETTE_AREA,
      data: {
        id: 'hermespace.open',
        label: 'Hermespace: Open',
        keywords: ['hermespace', 'pocket', 'pulse', 'access'],
        run: function () {
          host.navigate(ROUTE_PATH)
        }
      }
    })
    ctx.register({
      id: 'cmd-socket',
      area: PALETTE_AREA,
      data: {
        id: 'hermespace.socket',
        label: 'Hermespace: Socket hint (serve :8764)',
        keywords: ['hermespace', 'serve', '8764', 'tunnel'],
        run: function () {
          host.notify({
            kind: 'info',
            message: 'Agent host: hs view --serve --port 8764 · Remote: also tunnel 8764'
          })
        }
      }
    })
  }
}
