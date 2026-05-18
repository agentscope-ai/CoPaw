const z = window.QwenPaw.host, t = z.React, Z = z.antd, T = z.getApiUrl, B = z.getApiToken, { Button: R, Card: ee, Space: F, Table: te, Typography: ne, message: p, Modal: ae, Checkbox: re } = Z, { Title: se, Text: m, Paragraph: oe } = ne;
function $() {
  const i = {}, o = B == null ? void 0 : B();
  return o && (i.Authorization = `Bearer ${o}`), i;
}
async function _(i) {
  const o = await fetch(T(i), { headers: $() });
  if (!o.ok)
    throw new Error(`${o.status} ${await o.text()}`);
  return o.json();
}
async function J(i, o) {
  const u = await fetch(T(i), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...$() },
    body: JSON.stringify(o)
  }), h = await u.text();
  let s = null;
  try {
    s = h ? JSON.parse(h) : null;
  } catch {
    s = { raw: h };
  }
  if (!u.ok)
    throw new Error(typeof (s == null ? void 0 : s.detail) == "string" ? s.detail : h);
  return s;
}
const ie = 192, le = 208;
function ce({ folder: i }) {
  const o = t.useRef(null), [u, h] = t.useState(!1);
  return t.useEffect(() => {
    let s = !1;
    h(!1);
    const E = o.current;
    if (!E) return;
    const k = E.getContext("2d");
    if (k)
      return (async () => {
        try {
          const D = T(
            `/qwenpaw-pet/pets/${encodeURIComponent(i)}/spritesheet`
          ), P = await fetch(D, { headers: $() });
          if (!P.ok || s) throw new Error(String(P.status));
          const x = await P.blob(), b = await createImageBitmap(x);
          if (s) {
            b.close();
            return;
          }
          const S = 96, l = 104;
          E.width = S, E.height = l, k.imageSmoothingEnabled = !1, k.clearRect(0, 0, S, l), k.drawImage(b, 0, 0, ie, le, 0, 0, S, l), b.close();
        } catch {
          s || h(!0);
        }
      })(), () => {
        s = !0;
      };
  }, [i]), u ? t.createElement(m, { type: "secondary" }, "—") : t.createElement("canvas", {
    ref: o,
    width: 96,
    height: 104,
    style: {
      display: "block",
      borderRadius: 8,
      border: "1px solid rgba(0,0,0,0.08)",
      background: "rgba(0,0,0,0.02)",
      imageRendering: "pixelated"
    }
  });
}
function pe() {
  const [i, o] = t.useState([]), [u, h] = t.useState(""), [s, E] = t.useState(null), [k, D] = t.useState(!1), [P, x] = t.useState(!1), [b, S] = t.useState(!0), [l, N] = t.useState(!1), [w, C] = t.useState([]), [O, I] = t.useState(!1), q = t.useRef(null), v = t.useCallback(async () => {
    D(!0);
    try {
      const [e, n] = await Promise.all([
        _("/qwenpaw-pet/pets"),
        _("/qwenpaw-pet/status")
      ]);
      o(e.pets || []), h(e.petsDir || ""), E(n.desktop ?? null);
    } catch (e) {
      p.error((e == null ? void 0 : e.message) || String(e));
    } finally {
      D(!1);
    }
  }, []);
  t.useEffect(() => {
    v();
  }, [v]);
  const W = async () => {
    try {
      const e = await J("/qwenpaw-pet/desktop/start", {}), n = e == null ? void 0 : e.desktop, a = [e == null ? void 0 : e.message, e == null ? void 0 : e.hint].filter(Boolean).join(" ");
      e != null && e.alreadyRunning && (n != null && n.ok) ? p.success(a || "Desktop pet is already running.") : (e == null ? void 0 : e.launchAttempted) === !1 && !(n != null && n.ok) ? p.error(a || "Could not start the desktop pet.") : n != null && n.ok ? p.success(a || "Desktop pet is ready.") : p.warning(
        a || "Desktop may still be starting; check pet-desktop.log if needed."
      ), await v();
    } catch (e) {
      p.error((e == null ? void 0 : e.message) || String(e));
    }
  }, U = () => {
    C([]), S(!0), I(!1), x(!0);
  }, L = async (e, n, a) => {
    const r = n ? `${n}/${e.name}` : e.name;
    if (e.isFile) {
      const c = await new Promise(
        (y, d) => e.file(y, d)
      );
      a.push({ file: c, path: r });
      return;
    }
    if (!e.isDirectory) return;
    const f = e.createReader();
    for (; ; ) {
      const c = await new Promise(
        (y, d) => f.readEntries(y, d)
      );
      if (c.length === 0) break;
      for (const y of c)
        await L(y, r, a);
    }
  }, G = async (e) => {
    var f, c, y;
    if (e.preventDefault(), I(!1), l) return;
    const n = (f = e.dataTransfer) == null ? void 0 : f.items, a = (c = e.dataTransfer) == null ? void 0 : c.files, r = [];
    if (n && n.length > 0)
      for (let d = 0; d < n.length; d++) {
        const g = n[d];
        if (g.kind !== "file") continue;
        const Q = (y = g.webkitGetAsEntry) == null ? void 0 : y.call(g);
        if (Q)
          await L(Q, "", r);
        else {
          const A = g.getAsFile();
          A && r.push({ file: A, path: A.name });
        }
      }
    else if (a)
      for (let d = 0; d < a.length; d++) {
        const g = a[d];
        r.push({ file: g, path: g.name });
      }
    if (r.length === 0) {
      p.warning("Drop a folder or a .zip file.");
      return;
    }
    C(r);
  }, H = (e) => {
    e.preventDefault(), l || I(!0);
  }, K = (e) => {
    e.preventDefault(), I(!1);
  }, j = () => {
    var e;
    l || (e = q.current) == null || e.click();
  }, M = (e) => {
    var r;
    const n = (r = e.target) == null ? void 0 : r.files;
    if (!n || n.length === 0) return;
    const a = [];
    for (let f = 0; f < n.length; f++) {
      const c = n[f];
      a.push({ file: c, path: c.name });
    }
    C(a), e.target.value = "";
  }, V = async () => {
    if (w.length === 0) {
      p.warning("Drop a folder or choose a .zip file first.");
      return;
    }
    N(!0);
    try {
      const e = new FormData();
      for (const { file: f, path: c } of w)
        e.append("files", f, c);
      e.append("replace", b ? "true" : "false");
      const n = await fetch(T("/qwenpaw-pet/import-pet-upload"), {
        method: "POST",
        headers: $(),
        body: e
      }), a = await n.text();
      let r = null;
      try {
        r = a ? JSON.parse(a) : null;
      } catch {
        r = { raw: a };
      }
      if (!n.ok)
        throw new Error(typeof (r == null ? void 0 : r.detail) == "string" ? r.detail : a);
      p.success(
        `Imported "${r.displayName || r.petId}" → ${r.path}`
      ), x(!1), C([]), await v();
    } catch (e) {
      p.error((e == null ? void 0 : e.message) || String(e));
    } finally {
      N(!1);
    }
  }, X = async (e) => {
    const n = e.folder;
    try {
      const a = await J("/qwenpaw-pet/switch-pet", { pet_id: n });
      if (a && a.ok === !1)
        throw new Error(a.error || a.detail || "switch failed");
      p.success(`Switched to "${e.displayName}" (${n})`), await v();
    } catch (a) {
      p.error((a == null ? void 0 : a.message) || String(a));
    }
  }, Y = [
    {
      title: "Preview",
      key: "preview",
      width: 112,
      render: (e, n) => t.createElement(ce, { key: n.folder, folder: n.folder })
    },
    { title: "Name", dataIndex: "displayName", key: "displayName" },
    { title: "Folder", dataIndex: "folder", key: "folder" },
    {
      title: "pet.json id",
      key: "manifestId",
      render: (e, n) => n.manifestId ? String(n.manifestId) : t.createElement(m, { type: "secondary" }, "—")
    },
    {
      title: "Action",
      key: "act",
      render: (e, n) => t.createElement(
        R,
        { type: "primary", size: "small", onClick: () => void X(n) },
        "Switch"
      )
    }
  ];
  return t.createElement(
    ee,
    { style: { maxWidth: 880, margin: "24px auto" } },
    t.createElement(
      F,
      { direction: "vertical", size: "large", style: { width: "100%" } },
      [
        t.createElement(
          "div",
          { key: "h" },
          t.createElement(
            se,
            { level: 3, style: { marginBottom: 4 } },
            "QwenPaw Pet"
          ),
          t.createElement(
            oe,
            { type: "secondary", style: { marginBottom: 0 } },
            "Installed pets live under your QwenPaw working directory. Start the desktop bridge, then switch the floating pet without restarting QwenPaw."
          )
        ),
        t.createElement(
          F,
          { key: "actions", wrap: !0 },
          t.createElement(
            R,
            { type: "primary", onClick: W },
            "Start desktop pet"
          ),
          t.createElement(R, { onClick: U }, "Import pet"),
          t.createElement(
            R,
            { onClick: () => void v(), loading: k },
            "Refresh"
          )
        ),
        t.createElement(
          "div",
          { key: "meta" },
          t.createElement(
            m,
            { type: "secondary" },
            "Pets directory: "
          ),
          t.createElement(m, { code: !0 }, u || "—")
        ),
        t.createElement(
          "div",
          { key: "dh" },
          t.createElement(m, { strong: !0 }, "Desktop health: "),
          t.createElement(
            m,
            { type: s != null && s.ok ? "success" : "warning" },
            s ? JSON.stringify(s) : "unknown (refresh)"
          )
        ),
        t.createElement(te, {
          key: "tbl",
          rowKey: "folder",
          loading: k,
          dataSource: i,
          columns: Y,
          pagination: !1,
          locale: {
            emptyText: "No pets found. Run: qwenpaw-pet install-pet …"
          }
        }),
        t.createElement(
          ae,
          {
            key: "import-modal",
            title: "Import pet",
            open: P,
            onOk: () => void V(),
            okText: "Import",
            okButtonProps: { loading: l },
            cancelButtonProps: { disabled: l },
            onCancel: () => {
              l || x(!1);
            },
            destroyOnClose: !0
          },
          t.createElement(
            F,
            { direction: "vertical", style: { width: "100%" } },
            t.createElement(
              "div",
              {
                role: "button",
                tabIndex: 0,
                onClick: j,
                onDrop: G,
                onDragOver: H,
                onDragLeave: K,
                onKeyDown: (e) => {
                  (e.key === "Enter" || e.key === " ") && (e.preventDefault(), j());
                },
                style: {
                  border: `2px dashed ${O ? "#1677ff" : "#d9d9d9"}`,
                  borderRadius: 8,
                  padding: "32px 16px",
                  textAlign: "center",
                  cursor: l ? "not-allowed" : "pointer",
                  background: O ? "rgba(22, 119, 255, 0.06)" : "#fafafa",
                  transition: "border-color .15s ease, background .15s ease",
                  userSelect: "none",
                  color: O ? "#1677ff" : void 0
                }
              },
              // Line-art cube icon (matches the dropzone reference)
              t.createElement(
                "svg",
                {
                  width: 48,
                  height: 48,
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "currentColor",
                  strokeWidth: 1.5,
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  style: {
                    display: "block",
                    margin: "0 auto 12px",
                    opacity: 0.7
                  }
                },
                t.createElement("path", {
                  d: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
                }),
                t.createElement("polyline", {
                  points: "3.27 6.96 12 12.01 20.73 6.96"
                }),
                t.createElement("line", {
                  x1: "12",
                  y1: "22.08",
                  x2: "12",
                  y2: "12"
                })
              ),
              t.createElement(
                "div",
                {
                  style: {
                    fontSize: 16,
                    fontWeight: 600,
                    marginBottom: 4
                  }
                },
                "Drop a folder or .zip file here"
              ),
              t.createElement(
                m,
                { type: "secondary" },
                "or click to choose a .zip"
              )
            ),
            t.createElement("input", {
              ref: q,
              type: "file",
              accept: ".zip,application/zip",
              style: { display: "none" },
              onChange: M
            }),
            w.length === 0 ? t.createElement(
              m,
              { type: "secondary", style: { fontSize: 12 } },
              "Folder or unzipped archive must contain pet.json and spritesheet.webp (1536×1872)."
            ) : t.createElement(
              m,
              null,
              w.length === 1 ? `Selected: ${w[0].path}` : `Selected: ${w.length} files (root: ${w[0].path.split("/")[0] || w[0].path})`
            ),
            t.createElement(
              re,
              {
                checked: b,
                onChange: (e) => S(!!e.target.checked),
                disabled: l
              },
              "Replace if a pet with the same id already exists"
            )
          )
        )
      ]
    )
  );
}
class de {
  constructor() {
    this.id = "qwenpaw-pet";
  }
  setup() {
    var o, u;
    (u = (o = window.QwenPaw).registerRoutes) == null || u.call(o, this.id, [
      {
        path: "/plugin/qwenpaw-pet/pets",
        component: pe,
        label: "Pet",
        icon: "🐾",
        priority: 42
      }
    ]);
  }
}
new de().setup();
