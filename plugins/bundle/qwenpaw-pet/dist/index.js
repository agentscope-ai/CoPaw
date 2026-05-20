const _ = "language", H = "qwenpaw-pet-language-change";
function j() {
  try {
    return localStorage.getItem(_) || "";
  } catch {
    return "";
  }
}
function se() {
  const t = "__qwenpawPetLanguageHook", r = Storage.prototype;
  if (r[t]) return;
  const l = r.setItem;
  r.setItem = function(i, a) {
    l.call(this, i, a), i === _ && window.dispatchEvent(
      new CustomEvent(H, { detail: a })
    );
  }, r[t] = !0;
}
function ie(t) {
  se();
  let r = j();
  const l = (d) => {
    d !== r && (r = d, t(d));
  }, i = (d) => {
    l(String(d.detail ?? ""));
  }, a = (d) => {
    d.key === _ && l(d.newValue ?? "");
  };
  window.addEventListener(H, i), window.addEventListener("storage", a);
  const c = window.setInterval(() => {
    l(j());
  }, 500);
  return () => {
    window.removeEventListener(H, i), window.removeEventListener("storage", a), window.clearInterval(c);
  };
}
const J = {
  en: {
    routeLabel: "Pet",
    title: "QwenPaw Pet",
    intro: "Installed pets live under your QwenPaw working directory. Start the desktop bridge, then switch the floating pet without restarting QwenPaw.",
    startDesktop: "Start desktop pet",
    importPet: "Import pet",
    refresh: "Refresh",
    petsDirectory: "Pets directory:",
    desktopHealth: "Desktop health:",
    desktopUnknown: "unknown (refresh)",
    colPreview: "Preview",
    colName: "Name",
    colFolder: "Folder",
    colManifestId: "pet.json id",
    colAction: "Action",
    switch: "Switch",
    tableEmpty: "No pets found. Run: qwenpaw-pet install-pet …",
    desktopAlreadyRunning: "Desktop pet is already running.",
    desktopStartFailed: "Could not start the desktop pet.",
    desktopReady: "Desktop pet is ready.",
    desktopStarting: "Desktop may still be starting; check pet-desktop.log if needed.",
    dropFolderOrZip: "Drop a folder or a .zip file.",
    importChooseFirst: "Drop a folder or choose a .zip file first.",
    importSuccess: 'Imported "{name}" → {path}',
    switchSuccess: 'Switched to "{name}" ({petId})',
    switchFailed: "switch failed",
    modalImportTitle: "Import pet",
    modalImportOk: "Import",
    dropzoneTitle: "Drop a folder or .zip file here",
    dropzoneHint: "or click to choose a .zip",
    importFormatHint: "Folder or unzipped archive must contain pet.json and spritesheet.webp (1536×1872).",
    selectedOne: "Selected: {path}",
    selectedMany: "Selected: {count} files (root: {root})",
    importReplace: "Replace if a pet with the same id already exists"
  },
  zh: {
    routeLabel: "宠物",
    title: "QwenPaw 桌面宠物",
    intro: "已安装的宠物位于 QwenPaw 工作目录下。启动桌面桥接后，可在不重启 QwenPaw 的情况下切换悬浮宠物。",
    startDesktop: "启动桌面宠物",
    importPet: "导入宠物",
    refresh: "刷新",
    petsDirectory: "宠物目录：",
    desktopHealth: "桌面服务状态：",
    desktopUnknown: "未知（请刷新）",
    colPreview: "预览",
    colName: "名称",
    colFolder: "文件夹",
    colManifestId: "pet.json id",
    colAction: "操作",
    switch: "切换",
    tableEmpty: "未找到宠物。请运行：qwenpaw-pet install-pet …",
    desktopAlreadyRunning: "桌面宠物已在运行。",
    desktopStartFailed: "无法启动桌面宠物。",
    desktopReady: "桌面宠物已就绪。",
    desktopStarting: "桌面可能仍在启动中；如有问题请查看 pet-desktop.log。",
    dropFolderOrZip: "请拖入文件夹或 .zip 文件。",
    importChooseFirst: "请先拖入文件夹或选择 .zip 文件。",
    importSuccess: "已导入「{name}」→ {path}",
    switchSuccess: "已切换至「{name}」（{petId}）",
    switchFailed: "切换失败",
    modalImportTitle: "导入宠物",
    modalImportOk: "导入",
    dropzoneTitle: "将文件夹或 .zip 拖放到此处",
    dropzoneHint: "或点击选择 .zip 文件",
    importFormatHint: "文件夹或解压后的目录需包含 pet.json 与 spritesheet.webp（1536×1872）。",
    selectedOne: "已选择：{path}",
    selectedMany: "已选择：{count} 个文件（根目录：{root}）",
    importReplace: "若已存在相同 id 的宠物则覆盖"
  }
};
function le(t) {
  return String(t || "").trim().split("-")[0].toLowerCase() === "zh" ? "zh" : "en";
}
function B(t) {
  return le(t ?? j());
}
function V(t, r, l) {
  let i = J[t][r] ?? J.en[r];
  if (l)
    for (const [a, c] of Object.entries(l))
      i = i.split(`{${a}}`).join(String(c));
  return i;
}
function ce(t) {
  const [r, l] = t.useState(
    () => B()
  );
  t.useEffect(() => {
    const a = (c) => {
      l((d) => {
        const S = B(c);
        return d === S ? d : S;
      });
    };
    return ie((c) => a(c));
  }, []);
  const i = t.useCallback(
    (a, c) => V(r, a, c),
    [r]
  );
  return { locale: r, tr: i };
}
const z = window.QwenPaw.host, n = z.React, pe = z.antd, L = z.getApiUrl, N = z.getApiToken, { Button: F, Card: de, Space: q, Table: ue, Typography: fe, message: f, Modal: me, Checkbox: we } = pe, { Title: he, Text: h, Paragraph: ge } = fe;
function ye() {
  var t, r, l;
  try {
    const i = ((t = window.sessionStorage) == null ? void 0 : t.getItem("qwenpaw-agent-storage")) ?? ((r = window.localStorage) == null ? void 0 : r.getItem("qwenpaw-agent-storage"));
    if (!i) return null;
    const a = JSON.parse(i), c = (l = a == null ? void 0 : a.state) == null ? void 0 : l.selectedAgent;
    return typeof c == "string" && c ? c : null;
  } catch {
    return null;
  }
}
function R() {
  const t = {}, r = N == null ? void 0 : N();
  r && (t.Authorization = `Bearer ${r}`);
  const l = ye();
  return l && (t["X-Agent-Id"] = l), t;
}
async function W(t) {
  const r = await fetch(L(t), { headers: R() });
  if (!r.ok)
    throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
async function K(t, r) {
  const l = await fetch(L(t), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...R() },
    body: JSON.stringify(r)
  }), i = await l.text();
  let a = null;
  try {
    a = i ? JSON.parse(i) : null;
  } catch {
    a = { raw: i };
  }
  if (!l.ok)
    throw new Error(typeof (a == null ? void 0 : a.detail) == "string" ? a.detail : i);
  return a;
}
const ke = 192, Ee = 208;
function Se({ folder: t }) {
  const r = n.useRef(null), [l, i] = n.useState(!1);
  return n.useEffect(() => {
    let a = !1;
    i(!1);
    const c = r.current;
    if (!c) return;
    const d = c.getContext("2d");
    if (d)
      return (async () => {
        try {
          const S = L(
            `/qwenpaw-pet/pets/${encodeURIComponent(t)}/spritesheet`
          ), v = await fetch(S, { headers: R() });
          if (!v.ok || a) throw new Error(String(v.status));
          const A = await v.blob(), b = await createImageBitmap(A);
          if (a) {
            b.close();
            return;
          }
          const I = 96, P = 104;
          c.width = I, c.height = P, d.imageSmoothingEnabled = !1, d.clearRect(0, 0, I, P), d.drawImage(b, 0, 0, ke, Ee, 0, 0, I, P), b.close();
        } catch {
          a || i(!0);
        }
      })(), () => {
        a = !0;
      };
  }, [t]), l ? n.createElement(h, { type: "secondary" }, "—") : n.createElement("canvas", {
    ref: r,
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
function be() {
  const { tr: t } = ce(n), [r, l] = n.useState([]), [i, a] = n.useState(""), [c, d] = n.useState(null), [S, v] = n.useState(!1), [A, b] = n.useState(!1), [I, P] = n.useState(!0), [g, M] = n.useState(!1), [y, C] = n.useState([]), [O, x] = n.useState(!1), Q = n.useRef(null), D = n.useCallback(async () => {
    v(!0);
    try {
      const [e, o] = await Promise.all([
        W("/qwenpaw-pet/pets"),
        W("/qwenpaw-pet/status")
      ]);
      l(e.pets || []), a(e.petsDir || ""), d(o.desktop ?? null);
    } catch (e) {
      f.error((e == null ? void 0 : e.message) || String(e));
    } finally {
      v(!1);
    }
  }, []);
  n.useEffect(() => {
    D();
  }, [D]);
  const Z = async () => {
    try {
      const e = await K("/qwenpaw-pet/desktop/start", {}), o = e == null ? void 0 : e.desktop, s = [e == null ? void 0 : e.message, e == null ? void 0 : e.hint].filter(Boolean).join(" ");
      e != null && e.alreadyRunning && (o != null && o.ok) ? f.success(s || t("desktopAlreadyRunning")) : (e == null ? void 0 : e.launchAttempted) === !1 && !(o != null && o.ok) ? f.error(s || t("desktopStartFailed")) : o != null && o.ok ? f.success(s || t("desktopReady")) : f.warning(s || t("desktopStarting")), await D();
    } catch (e) {
      f.error((e == null ? void 0 : e.message) || String(e));
    }
  }, X = () => {
    C([]), P(!0), x(!1), b(!0);
  }, U = async (e, o, s) => {
    const p = o ? `${o}/${e.name}` : e.name;
    if (e.isFile) {
      const u = await new Promise(
        (k, m) => e.file(k, m)
      );
      s.push({ file: u, path: p });
      return;
    }
    if (!e.isDirectory) return;
    const w = e.createReader();
    for (; ; ) {
      const u = await new Promise(
        (k, m) => w.readEntries(k, m)
      );
      if (u.length === 0) break;
      for (const k of u)
        await U(k, p, s);
    }
  }, Y = async (e) => {
    var w, u, k;
    if (e.preventDefault(), x(!1), g) return;
    const o = (w = e.dataTransfer) == null ? void 0 : w.items, s = (u = e.dataTransfer) == null ? void 0 : u.files, p = [];
    if (o && o.length > 0)
      for (let m = 0; m < o.length; m++) {
        const E = o[m];
        if (E.kind !== "file") continue;
        const G = (k = E.webkitGetAsEntry) == null ? void 0 : k.call(E);
        if (G)
          await U(G, "", p);
        else {
          const T = E.getAsFile();
          T && p.push({ file: T, path: T.name });
        }
      }
    else if (s)
      for (let m = 0; m < s.length; m++) {
        const E = s[m];
        p.push({ file: E, path: E.name });
      }
    if (p.length === 0) {
      f.warning(t("dropFolderOrZip"));
      return;
    }
    C(p);
  }, ee = (e) => {
    e.preventDefault(), g || x(!0);
  }, te = (e) => {
    e.preventDefault(), x(!1);
  }, $ = () => {
    var e;
    g || (e = Q.current) == null || e.click();
  }, ne = (e) => {
    var p;
    const o = (p = e.target) == null ? void 0 : p.files;
    if (!o || o.length === 0) return;
    const s = [];
    for (let w = 0; w < o.length; w++) {
      const u = o[w];
      s.push({ file: u, path: u.name });
    }
    C(s), e.target.value = "";
  }, oe = async () => {
    if (y.length === 0) {
      f.warning(t("importChooseFirst"));
      return;
    }
    M(!0);
    try {
      const e = new FormData();
      for (const { file: w, path: u } of y)
        e.append("files", w, u);
      e.append("replace", I ? "true" : "false");
      const o = await fetch(L("/qwenpaw-pet/import-pet-upload"), {
        method: "POST",
        headers: R(),
        body: e
      }), s = await o.text();
      let p = null;
      try {
        p = s ? JSON.parse(s) : null;
      } catch {
        p = { raw: s };
      }
      if (!o.ok)
        throw new Error(typeof (p == null ? void 0 : p.detail) == "string" ? p.detail : s);
      f.success(
        t("importSuccess", {
          name: p.displayName || p.petId,
          path: p.path
        })
      ), b(!1), C([]), await D();
    } catch (e) {
      f.error((e == null ? void 0 : e.message) || String(e));
    } finally {
      M(!1);
    }
  }, re = async (e) => {
    const o = e.folder;
    try {
      const s = await K("/qwenpaw-pet/switch-pet", { pet_id: o });
      if (s && s.ok === !1)
        throw new Error(s.error || s.detail || t("switchFailed"));
      f.success(
        t("switchSuccess", { name: e.displayName, petId: o })
      ), await D();
    } catch (s) {
      f.error((s == null ? void 0 : s.message) || String(s));
    }
  }, ae = n.useMemo(
    () => [
      {
        title: t("colPreview"),
        key: "preview",
        width: 112,
        render: (e, o) => n.createElement(Se, {
          key: o.folder,
          folder: o.folder
        })
      },
      { title: t("colName"), dataIndex: "displayName", key: "displayName" },
      { title: t("colFolder"), dataIndex: "folder", key: "folder" },
      {
        title: t("colManifestId"),
        key: "manifestId",
        render: (e, o) => o.manifestId ? String(o.manifestId) : n.createElement(h, { type: "secondary" }, "—")
      },
      {
        title: t("colAction"),
        key: "act",
        render: (e, o) => n.createElement(
          F,
          {
            type: "primary",
            size: "small",
            onClick: () => void re(o)
          },
          t("switch")
        )
      }
    ],
    [t]
  );
  return n.createElement(
    de,
    { style: { maxWidth: 880, margin: "24px auto" } },
    n.createElement(
      q,
      { direction: "vertical", size: "large", style: { width: "100%" } },
      [
        n.createElement(
          "div",
          { key: "h" },
          n.createElement(
            he,
            { level: 3, style: { marginBottom: 4 } },
            t("title")
          ),
          n.createElement(
            ge,
            { type: "secondary", style: { marginBottom: 0 } },
            t("intro")
          )
        ),
        n.createElement(
          q,
          { key: "actions", wrap: !0 },
          n.createElement(
            F,
            { type: "primary", onClick: Z },
            t("startDesktop")
          ),
          n.createElement(F, { onClick: X }, t("importPet")),
          n.createElement(
            F,
            { onClick: () => void D(), loading: S },
            t("refresh")
          )
        ),
        n.createElement(
          "div",
          { key: "meta" },
          n.createElement(
            h,
            { type: "secondary" },
            t("petsDirectory") + " "
          ),
          n.createElement(h, { code: !0 }, i || "—")
        ),
        n.createElement(
          "div",
          { key: "dh" },
          n.createElement(h, { strong: !0 }, t("desktopHealth") + " "),
          n.createElement(
            h,
            { type: c != null && c.ok ? "success" : "warning" },
            c ? JSON.stringify(c) : t("desktopUnknown")
          )
        ),
        n.createElement(ue, {
          key: "tbl",
          rowKey: "folder",
          loading: S,
          dataSource: r,
          columns: ae,
          pagination: !1,
          locale: {
            emptyText: t("tableEmpty")
          }
        }),
        n.createElement(
          me,
          {
            key: "import-modal",
            title: t("modalImportTitle"),
            open: A,
            onOk: () => void oe(),
            okText: t("modalImportOk"),
            okButtonProps: { loading: g },
            cancelButtonProps: { disabled: g },
            onCancel: () => {
              g || b(!1);
            },
            destroyOnClose: !0
          },
          n.createElement(
            q,
            { direction: "vertical", style: { width: "100%" } },
            n.createElement(
              "div",
              {
                role: "button",
                tabIndex: 0,
                onClick: $,
                onDrop: Y,
                onDragOver: ee,
                onDragLeave: te,
                onKeyDown: (e) => {
                  (e.key === "Enter" || e.key === " ") && (e.preventDefault(), $());
                },
                style: {
                  border: `2px dashed ${O ? "#1677ff" : "#d9d9d9"}`,
                  borderRadius: 8,
                  padding: "32px 16px",
                  textAlign: "center",
                  cursor: g ? "not-allowed" : "pointer",
                  background: O ? "rgba(22, 119, 255, 0.06)" : "#fafafa",
                  transition: "border-color .15s ease, background .15s ease",
                  userSelect: "none",
                  color: O ? "#1677ff" : void 0
                }
              },
              // Line-art cube icon (matches the dropzone reference)
              n.createElement(
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
                n.createElement("path", {
                  d: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
                }),
                n.createElement("polyline", {
                  points: "3.27 6.96 12 12.01 20.73 6.96"
                }),
                n.createElement("line", {
                  x1: "12",
                  y1: "22.08",
                  x2: "12",
                  y2: "12"
                })
              ),
              n.createElement(
                "div",
                {
                  style: {
                    fontSize: 16,
                    fontWeight: 600,
                    marginBottom: 4
                  }
                },
                t("dropzoneTitle")
              ),
              n.createElement(
                h,
                { type: "secondary" },
                t("dropzoneHint")
              )
            ),
            n.createElement("input", {
              ref: Q,
              type: "file",
              accept: ".zip,application/zip",
              style: { display: "none" },
              onChange: ne
            }),
            y.length === 0 ? n.createElement(
              h,
              { type: "secondary", style: { fontSize: 12 } },
              t("importFormatHint")
            ) : n.createElement(
              h,
              null,
              y.length === 1 ? t("selectedOne", { path: y[0].path }) : t("selectedMany", {
                count: y.length,
                root: y[0].path.split("/")[0] || y[0].path
              })
            ),
            n.createElement(
              we,
              {
                checked: I,
                onChange: (e) => P(!!e.target.checked),
                disabled: g
              },
              t("importReplace")
            )
          )
        )
      ]
    )
  );
}
class ve {
  constructor() {
    this.id = "qwenpaw-pet";
  }
  setup() {
    var l, i;
    const r = B();
    (i = (l = window.QwenPaw).registerRoutes) == null || i.call(l, this.id, [
      {
        path: "/plugin/qwenpaw-pet/pets",
        component: be,
        label: V(r, "routeLabel"),
        icon: "🐾",
        priority: 42
      }
    ]);
  }
}
new ve().setup();
