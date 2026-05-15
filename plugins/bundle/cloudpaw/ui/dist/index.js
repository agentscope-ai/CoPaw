function mt() {
  var je, Me, Ne, He;
  const { React: e, antd: z, antdIcons: b, getApiUrl: L, getApiToken: H } = window.QwenPaw.host, {
    Card: B,
    Table: le,
    Tag: c,
    Typography: d,
    Space: A,
    Button: x,
    Input: S,
    Radio: fe,
    Collapse: ht,
    Descriptions: Y,
    Tooltip: be,
    Spin: pe,
    message: ke
  } = z, { Text: D } = d, { TextArea: Ke } = S, { useState: C, useMemo: ae, useCallback: V, useRef: Et } = e, {
    InfoCircleOutlined: ve,
    DownOutlined: Ie,
    RightOutlined: qe,
    CheckCircleOutlined: ge,
    FieldTimeOutlined: ye,
    FileTextOutlined: _e
  } = b || {};
  function Te(t) {
    var a, f;
    const n = (f = (a = t == null ? void 0 : t.content) == null ? void 0 : a[0]) == null ? void 0 : f.data, s = n == null ? void 0 : n.arguments;
    if (typeof s == "string")
      try {
        return JSON.parse(s);
      } catch {
        return {};
      }
    return s ?? {};
  }
  function Qe() {
    return window.currentSessionId ?? null;
  }
  function X(t) {
    return typeof t == "string" ? t : t && typeof t == "object" && "text" in t ? t.text : String(t ?? "");
  }
  function Ge(t) {
    if (t == null) return !0;
    const n = X(t).trim();
    return !!(!n || /^[¥$]?0+(\.0+)?$/.test(n) || /^[-–—]+$/.test(n));
  }
  async function Ye(t, n) {
    try {
      const s = H(), a = {
        "Content-Type": "application/json"
      };
      return s && (a.Authorization = `Bearer ${s}`), (await fetch(L("/interaction"), {
        method: "POST",
        headers: a,
        body: JSON.stringify({ session_id: t, result: n })
      })).ok;
    } catch {
      return !1;
    }
  }
  function ze(t) {
    if (!t) return null;
    if (typeof t == "string")
      try {
        const n = JSON.parse(t);
        if (Array.isArray(n)) {
          const s = n.find((a) => (a == null ? void 0 : a.type) === "text" && (a == null ? void 0 : a.text));
          return (s == null ? void 0 : s.text) ?? null;
        }
        if (typeof n == "string") return n;
      } catch {
        return t;
      }
    if (Array.isArray(t)) {
      const n = t.find((s) => (s == null ? void 0 : s.type) === "text" && (s == null ? void 0 : s.text));
      return (n == null ? void 0 : n.text) ?? null;
    }
    return null;
  }
  function Ve(t) {
    var l, r;
    if (!t || t.length < 2) return null;
    const n = (r = (l = t[1]) == null ? void 0 : l.data) == null ? void 0 : r.output, s = ze(n);
    if (!s) return null;
    if (s.startsWith("Error:")) return s;
    const a = s.match(/^用户选择了「(.+?)」并确认部署$/);
    if (a) return `已确认部署「${a[1]}」`;
    const f = s.match(/^用户选择「(.+?)」并要求调整[：:](.+)$/);
    if (f) return `已选择「${f[1]}」并调整：${f[2]}`;
    if (s === "用户确认部署") return "已确认部署";
    const p = s.match(/^用户要求调整资源[：:](.+)$/);
    return p ? `已反馈调整意见：${p[1]}` : "已确认";
  }
  const Pe = [
    "资源类型",
    "资源用途",
    "规格",
    "地域",
    "数量",
    "计费方式",
    "时长",
    "原价",
    "优惠",
    "预估算费用"
  ], Xe = new Set(Pe.map((t) => t.toLowerCase()));
  function Se(t) {
    if (!Array.isArray(t) || t.length !== 10) return !1;
    const n = X(t[0]).trim().toLowerCase();
    return Xe.has(n);
  }
  function $e(t) {
    if (!Array.isArray(t) || t.length !== 10) return !1;
    const n = X(t[0]).trim();
    return /^(合计|总计|total)/i.test(n);
  }
  function Ze(t) {
    const n = [];
    let s = [];
    for (const a of t)
      s.push(a), $e(a) && (n.push(s), s = []);
    return s.length > 0 && (n.length > 0 ? n[n.length - 1].push(...s) : n.push(s)), n.length > 0 ? n : [t];
  }
  function et(t) {
    return typeof t == "string" ? t : t && typeof t == "object" && t.text ? t.url ? e.createElement("a", {
      href: t.url,
      target: "_blank",
      rel: "noopener noreferrer"
    }, t.text) : t.text : String(t ?? "");
  }
  function tt({ data: t }) {
    var Je, Fe, Ue;
    const [n, s] = C("confirm"), [a, f] = C(""), [p, l] = C(!1), [r, P] = C(null), [j, F] = C({}), U = e.useRef(!1), M = e.useRef(null), [, te] = C(0), J = t == null ? void 0 : t.content, k = J && J.length >= 2 && ((Fe = (Je = J[1]) == null ? void 0 : Je.data) == null ? void 0 : Fe.output), v = ae(
      () => Ve(J),
      [J]
    ), N = U.current || k || v !== null, i = ae(() => {
      const w = Te(t), h = w == null ? void 0 : w.data;
      if (!h) return null;
      try {
        const y = typeof h == "string" ? JSON.parse(h) : h;
        let I;
        if (w.strategy_names)
          try {
            const T = typeof w.strategy_names == "string" ? JSON.parse(w.strategy_names) : w.strategy_names;
            I = Array.isArray(T) ? T : [];
          } catch {
            I = [];
          }
        else y != null && y.proposal_names ? I = y.proposal_names : I = [];
        const re = I.length >= 2 ? I.length : 0;
        let _;
        if (Array.isArray(y) && y.length > 0)
          if (Array.isArray(y[0]) && y[0].length === 10 && !Array.isArray(y[0][0])) {
            const O = y.filter((se) => !Se(se));
            if (O.filter((se) => $e(se)).length >= 2)
              _ = Ze(O);
            else if (re >= 2 && O.length >= re * 2) {
              const se = Math.ceil(O.length / re);
              _ = [];
              for (let de = 0; de < O.length; de += se)
                _.push(O.slice(de, de + se));
            } else
              _ = [O];
          } else
            _ = y.map(
              (O) => O.filter((ue) => Array.isArray(ue) && ue.length === 10 && !Se(ue))
            );
        else if (y != null && y.proposals)
          _ = y.proposals.map(
            (T) => T.filter((O) => !Se(O))
          );
        else
          return null;
        if (_ = _.filter((T) => T.length > 0), _.length === 0) return null;
        const Ae = ["方案一", "方案二", "方案三", "方案四", "方案五"];
        if (I.length < _.length)
          for (let T = I.length; T < _.length; T++)
            I.push(Ae[T] || `方案${T + 1}`);
        return { proposals: _, names: I };
      } catch {
        return null;
      }
    }, [t]), m = Qe(), u = (((Ue = i == null ? void 0 : i.proposals) == null ? void 0 : Ue.length) ?? 0) > 1, $ = V(async () => {
      if (!m || N || !i) return;
      const w = u ? r : 0, h = i.names[w ?? 0] || `方案${(w ?? 0) + 1}`;
      let y;
      n === "confirm" ? y = `用户选择了「${h}」并确认部署` : y = `用户选择「${h}」并要求调整：${a.trim() || "未填写具体要求"}`, l(!0);
      const I = await Ye(m, y);
      l(!1), I ? (U.current = !0, n === "confirm" ? M.current = `已确认部署「${h}」` : M.current = `已选择「${h}」并调整：${a.trim()}`, te((re) => re + 1), ke.success(n === "confirm" ? "已确认部署方案" : "已提交调整意见")) : ke.error("操作失败，请重试");
    }, [m, N, i, n, a, r, u]), me = (t == null ? void 0 : t.status) === "in_progress" || (t == null ? void 0 : t.status) === "created";
    if (!i)
      return me ? e.createElement(
        "div",
        {
          style: {
            width: "100%",
            borderRadius: 10,
            border: "1px solid #f0f0f0",
            background: "#fff",
            padding: "24px 16px",
            margin: "4px 0",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12
          }
        },
        e.createElement(pe, { size: "default" }),
        e.createElement(
          D,
          { type: "secondary", style: { fontSize: 13 } },
          "正在生成资源方案..."
        )
      ) : e.createElement(
        B,
        { size: "small", style: { margin: "4px 0" } },
        e.createElement(D, { type: "secondary" }, "无法解析方案数据")
      );
    const { proposals: ne, names: ie } = i, ce = Pe.map((w, h) => ({
      title: w,
      dataIndex: `col_${h}`,
      key: `col_${h}`,
      render: (y) => et(y),
      ellipsis: h < 3
    }));
    let W = "待确认", K = "processing";
    N && (K = "success", W = M.current || v || "已确认");
    const q = e.createElement(c, {
      color: K,
      style: { marginLeft: 4 }
    }, W), R = e.createElement(
      A,
      { size: 8 },
      e.createElement("span", null, "☁️"),
      e.createElement(
        D,
        { strong: !0, style: { fontSize: 14 } },
        N ? "资源配置方案" : "请确认您的资源配置方案"
      ),
      q
    ), Q = ne.map((w, h) => {
      const y = u ? r === h : !0, I = j[h] || !1, re = (E) => {
        const ee = X(E[0] || "").trim();
        return /^合计|^总计|^total/i.test(ee);
      }, _ = w.find(re), Ae = w.filter((E) => !re(E)), T = Ae.map((E) => ({
        type: X(E[0] || ""),
        purpose: X(E[1] || ""),
        spec: X(E[2] || ""),
        cost: E[9] ?? null
      })), O = _ ? X(_[9] ?? "") : "", ue = w.map((E, ee) => {
        const We = { key: ee };
        return E.forEach((dt, ft) => {
          We[`col_${ft}`] = dt;
        }), We;
      }), se = y ? "2px solid #1677ff" : "1px solid #e8e8e8", de = y ? "0 0 0 2px #e6f4ff" : "none";
      return e.createElement(
        "div",
        {
          key: h,
          style: {
            flex: 1,
            minWidth: 240,
            border: se,
            borderRadius: 8,
            cursor: u ? "pointer" : "default",
            transition: "all 0.2s ease",
            boxShadow: de,
            background: "#fff"
          },
          onClick: u ? () => P(h) : void 0
        },
        e.createElement(
          "div",
          { style: { padding: "10px 12px" } },
          // Proposal name
          e.createElement(D, {
            strong: !0,
            style: { fontSize: 14, display: "block", marginBottom: 8 }
          }, ie[h]),
          ...T.map(
            (E, ee) => e.createElement(
              "div",
              {
                key: ee,
                style: {
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "4px 0",
                  borderBottom: ee < T.length - 1 ? "1px solid #f5f5f5" : "none"
                }
              },
              e.createElement(
                "div",
                { style: { flex: 1, minWidth: 0 } },
                e.createElement("span", { style: { fontSize: 12, color: "#262626" } }, E.type),
                E.spec && e.createElement("span", {
                  style: { fontSize: 11, color: "#8c8c8c", marginLeft: 6 }
                }, E.spec)
              ),
              !Ge(E.cost) && e.createElement("span", {
                style: { fontSize: 12, color: "#595959", flexShrink: 0, marginLeft: 8 }
              }, X(E.cost))
            )
          ),
          // Total cost
          O && e.createElement(
            "div",
            {
              style: {
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: 6,
                paddingTop: 6,
                borderTop: "1px dashed #e8e8e8"
              }
            },
            e.createElement("span", { style: { fontSize: 12, fontWeight: 500 } }, "合计"),
            e.createElement("span", {
              style: { fontSize: 14, fontWeight: 700, color: "#fa541c" }
            }, O)
          ),
          // Details toggle
          e.createElement(
            "div",
            {
              style: {
                display: "flex",
                alignItems: "center",
                gap: 4,
                color: "#8c8c8c",
                fontSize: 12,
                cursor: "pointer",
                marginTop: 6
              },
              onClick: (E) => {
                E.stopPropagation(), F((ee) => ({ ...ee, [h]: !ee[h] }));
              }
            },
            e.createElement(I && Ie ? Ie : qe || "span", {
              style: { fontSize: 10 }
            }),
            e.createElement("span", null, `明细 · ${Ae.length} 项`)
          ),
          I && e.createElement(
            "div",
            {
              onClick: (E) => E.stopPropagation(),
              style: { marginTop: 4, maxHeight: 260, overflow: "auto" }
            },
            e.createElement(le, {
              columns: ce,
              dataSource: ue,
              pagination: !1,
              size: "small",
              scroll: { x: "max-content" }
            })
          )
        )
      );
    }), o = e.createElement(
      "div",
      {
        style: {
          background: "#fffbe6",
          border: "1px solid #ffe58f",
          borderRadius: 6,
          padding: "8px 12px",
          marginBottom: 10,
          display: "flex",
          alignItems: "flex-start",
          gap: 8
        }
      },
      ve ? e.createElement(ve, { style: { color: "#faad14", fontSize: 14, flexShrink: 0, marginTop: 1 } }) : e.createElement("span", null, "⚠️"),
      e.createElement("span", {
        style: { fontSize: 12, color: "#8c6e00", lineHeight: 1.5 }
      }, "在服务部署与配置过程中，可能因实际资源需求变化导致资源变配及费用调整，请及时关注实际资源使用情况与账单详情。")
    ), g = !N && m && !(u && r === null) && e.createElement(
      "div",
      null,
      e.createElement(
        "div",
        {
          style: { display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }
        },
        // Confirm option
        e.createElement(
          "div",
          {
            style: {
              flex: 1,
              minWidth: 140,
              border: `1px solid ${n === "confirm" ? "#1677ff" : "#e8e8e8"}`,
              borderRadius: 6,
              padding: "8px 12px",
              cursor: "pointer",
              transition: "all 0.15s ease",
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: n === "confirm" ? "#e6f4ff" : "transparent"
            },
            onClick: () => s("confirm")
          },
          e.createElement(fe, { checked: n === "confirm" }),
          e.createElement("span", { style: { fontSize: 13 } }, "确认部署")
        ),
        // Adjust option
        e.createElement(
          "div",
          {
            style: {
              flex: 1,
              minWidth: 140,
              border: `1px solid ${n === "adjust" ? "#1677ff" : "#e8e8e8"}`,
              borderRadius: 6,
              padding: "8px 12px",
              transition: "all 0.15s ease",
              background: n === "adjust" ? "#e6f4ff" : "transparent"
            }
          },
          e.createElement(
            "div",
            {
              style: { display: "flex", alignItems: "center", gap: 8, cursor: "pointer" },
              onClick: () => s("adjust")
            },
            e.createElement(fe, { checked: n === "adjust" }),
            e.createElement("span", { style: { fontSize: 13 } }, "调整资源")
          ),
          n === "adjust" && e.createElement(Ke, {
            value: a,
            onChange: (w) => f(w.target.value),
            placeholder: "请输入调整要求",
            autoSize: { minRows: 1, maxRows: 3 },
            style: { fontSize: 12, marginTop: 6 }
          })
        )
      ),
      // Footer
      e.createElement(
        "div",
        {
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: 8
          }
        },
        e.createElement(
          D,
          { type: "secondary", style: { fontSize: 11 } },
          u ? "一小时后未操作将自动选择第一个方案" : "一小时后未操作将自动确认部署"
        ),
        e.createElement(x, {
          type: "primary",
          size: "small",
          loading: p,
          onClick: $,
          disabled: n === "adjust" && !a.trim()
        }, n === "confirm" ? "确认部署" : "提交调整")
      )
    ), G = u && r === null && !N && e.createElement("div", {
      style: { textAlign: "center", padding: "8px 0 4px", color: "rgba(0,0,0,0.45)", fontSize: 12 }
    }, "请点击选择一个方案后继续操作");
    return e.createElement(
      "div",
      {
        style: {
          width: "100%",
          borderRadius: 10,
          border: "1px solid #f0f0f0",
          overflow: "hidden",
          background: "#fff",
          padding: "12px 16px",
          margin: "4px 0"
        }
      },
      // Header
      e.createElement("div", { style: { marginBottom: 10 } }, R),
      // Proposals grid
      e.createElement("div", {
        style: { display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }
      }, ...Q),
      G,
      o,
      !N && g
    );
  }
  function nt({ data: t }) {
    const [n, s] = C(null), [a, f] = C(!1), p = (t == null ? void 0 : t.status) === "in_progress" || (t == null ? void 0 : t.status) === "created", l = ae(() => {
      const i = Te(t);
      return (i == null ? void 0 : i.loop_dir) || null;
    }, [t]), r = ae(() => {
      var m, u, $;
      const i = ze(($ = (u = (m = t == null ? void 0 : t.content) == null ? void 0 : m[1]) == null ? void 0 : u.data) == null ? void 0 : $.output);
      if (!i) return null;
      try {
        return JSON.parse(i);
      } catch {
        return null;
      }
    }, [t]), P = (r == null ? void 0 : r.status) === "ok", j = (r == null ? void 0 : r.status) === "error", F = j ? (r == null ? void 0 : r.message) || "未知错误" : null, U = V(async () => {
      if (l)
        try {
          const i = H(), m = {};
          i && (m.Authorization = `Bearer ${i}`);
          const u = await fetch(
            L(`/prd?loop_dir=${encodeURIComponent(l)}`),
            { headers: m }
          );
          if (!u.ok) {
            f(!0);
            return;
          }
          const $ = await u.json();
          $ && Array.isArray($.userStories) ? (s($), f(!1)) : f(!0);
        } catch {
          f(!0);
        }
    }, [l]);
    if (e.useEffect(() => {
      !p && P && l && U();
    }, [p, P, l, U]), p)
      return e.createElement(
        "div",
        {
          style: {
            width: "100%",
            borderRadius: 10,
            border: "1px solid #f0f0f0",
            background: "#fff",
            padding: "24px 16px",
            margin: "4px 0",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12
          }
        },
        e.createElement(pe, { size: "default" }),
        e.createElement(
          D,
          { type: "secondary", style: { fontSize: 13 } },
          "正在更新 PRD..."
        )
      );
    if (j)
      return e.createElement(
        "div",
        {
          style: {
            width: "100%",
            borderRadius: 10,
            border: "1px solid #fff1f0",
            background: "#fff1f0",
            padding: "12px 16px",
            margin: "4px 0",
            display: "flex",
            alignItems: "center",
            gap: 8
          }
        },
        e.createElement(
          D,
          { type: "danger", style: { fontSize: 13 } },
          `PRD 格式错误，将会修正：${F}`
        )
      );
    if (!P || a || !n) return null;
    const M = n.userStories, te = [...M].sort((i, m) => (i.priority || 99) - (m.priority || 99)), J = M.filter((i) => i.passes).length, k = [
      {
        title: "状态",
        key: "status",
        width: 50,
        align: "center",
        render: (i, m) => {
          if (m.passes) {
            const $ = ge ? e.createElement(ge, { style: { color: "#52c41a", fontSize: 18 } }) : "✅";
            return e.createElement(be, { title: "已完成" }, $);
          }
          const u = ye ? e.createElement(ye, { style: { color: "#faad14", fontSize: 18 } }) : "🕐";
          return e.createElement(be, { title: "待处理" }, u);
        }
      },
      {
        title: "ID",
        dataIndex: "id",
        key: "id",
        width: 85,
        render: (i) => e.createElement(c, { color: "blue" }, i)
      },
      {
        title: "标题",
        dataIndex: "title",
        key: "title",
        render: (i) => e.createElement(D, { strong: !0 }, i)
      },
      {
        title: "优先级",
        key: "priority",
        width: 70,
        render: (i, m) => {
          const u = m.priority;
          return e.createElement(c, { color: "default" }, u != null ? String(u) : "-");
        }
      },
      {
        title: "描述",
        dataIndex: "description",
        key: "description",
        ellipsis: !0
      },
      {
        title: "验收标准",
        key: "acceptance",
        width: 200,
        render: (i, m) => {
          const u = m.acceptanceCriteria;
          return typeof u == "string" ? e.createElement(
            "div",
            { style: { fontSize: 12, color: "#666", whiteSpace: "pre-wrap" } },
            u.length > 100 ? u.slice(0, 100) + "..." : u
          ) : Array.isArray(u) ? e.createElement(
            "div",
            { style: { fontSize: 12, color: "#666" } },
            u.length > 2 ? u.slice(0, 2).join(", ") + "..." : u.join(", ")
          ) : "-";
        }
      }
    ], v = e.createElement(
      A,
      { size: 8 },
      _e ? e.createElement(_e, { style: { color: "#1677ff" } }) : null,
      e.createElement(
        "span",
        { style: { fontSize: 14 } },
        e.createElement(D, { strong: !0 }, n.project || "PRD")
      )
    ), N = e.createElement(le, {
      columns: k,
      dataSource: te.map((i) => ({ ...i, key: i.id })),
      size: "small",
      pagination: !1,
      scroll: { x: "max-content" },
      style: { marginBottom: 4 }
    });
    return e.createElement(
      "div",
      {
        style: {
          width: "100%",
          borderRadius: 10,
          border: "1px solid #f0f0f0",
          overflow: "hidden",
          background: "#fff",
          padding: "12px 16px",
          margin: "4px 0"
        }
      },
      e.createElement("div", { style: { marginBottom: 8 } }, v),
      e.createElement(Y, {
        size: "small",
        column: { xs: 1, sm: 2, md: 3 },
        style: { marginBottom: 12 },
        bordered: !1,
        items: [
          { key: "progress", label: "进度", children: `${J}/${M.length} 完成` }
        ]
      }),
      N,
      e.createElement(
        "div",
        { style: { fontSize: 11, color: "#8c8c8c", display: "flex", alignItems: "center", gap: 8 } },
        ge ? e.createElement(ge, { style: { color: "#52c41a", fontSize: 14 } }) : "✅",
        e.createElement("span", null, "已完成"),
        e.createElement("span", { style: { margin: "0 4px" } }, "·"),
        ye ? e.createElement(ye, { style: { color: "#faad14", fontSize: 14 } }) : "🕐",
        e.createElement("span", null, "待处理")
      )
    );
  }
  function rt({ data: t }) {
    var ne, ie, ce;
    const n = (t == null ? void 0 : t.status) || "", s = n === "in_progress" || n === "created", a = n === "completed" || n === "canceled" || n === "failed", f = e.useRef(null), p = ae(() => {
      var K, q, R;
      const W = (R = (q = (K = t == null ? void 0 : t.content) == null ? void 0 : K[0]) == null ? void 0 : q.data) == null ? void 0 : R.arguments;
      if (!W) return null;
      try {
        return JSON.parse(W);
      } catch {
        return null;
      }
    }, [(ce = (ie = (ne = t == null ? void 0 : t.content) == null ? void 0 : ne[0]) == null ? void 0 : ie.data) == null ? void 0 : ce.arguments]), l = ae(() => {
      var K;
      if (a && f.current) return f.current;
      const W = t == null ? void 0 : t.content;
      if (!Array.isArray(W)) return null;
      for (const q of W) {
        const R = (K = q == null ? void 0 : q.data) == null ? void 0 : K.output;
        if (!R) continue;
        let Q = "";
        if (Array.isArray(R)) {
          const o = R.find((g) => (g == null ? void 0 : g.type) === "text" && (g == null ? void 0 : g.text));
          Q = (o == null ? void 0 : o.text) || "";
        } else if (typeof R == "string")
          try {
            const o = JSON.parse(R);
            if (typeof o == "object" && (o != null && o.response_text)) return o;
            if (Array.isArray(o)) {
              const g = o.find((G) => (G == null ? void 0 : G.type) === "text" && (G == null ? void 0 : G.text));
              g != null && g.text && (Q = g.text);
            }
          } catch {
            Q = R;
          }
        if (Q)
          try {
            const o = JSON.parse(Q);
            return a && (f.current = o), o;
          } catch {
            return null;
          }
      }
      return null;
    }, [t == null ? void 0 : t.content, a]), r = (p == null ? void 0 : p.agent_alias) || "", P = (p == null ? void 0 : p.agent_url) || "", j = r || P || "远程 Agent", F = (l == null ? void 0 : l.response_text) || "", U = (l == null ? void 0 : l.task_state) || "", M = (l == null ? void 0 : l.error) || "", te = (l == null ? void 0 : l.event_count) || 0, J = {
      completed: "#52c41a",
      failed: "#ff4d4f",
      error: "#ff4d4f",
      canceled: "#faad14",
      working: "#1677ff"
    }, k = {
      completed: "已完成",
      failed: "失败",
      error: "出错",
      canceled: "已取消",
      working: "执行中"
    }, v = s ? "#1677ff" : J[U] || "#d9d9d9", N = s ? "执行中..." : k[U] || U || "完成", i = M ? `错误: ${M}` : F || "等待响应...", m = e.createElement(
      A,
      { size: 8 },
      e.createElement("span", null, "🔗"),
      e.createElement(
        D,
        { strong: !0, style: { fontSize: 14 } },
        `A2A 调用: ${j}`
      ),
      e.createElement(c, { color: v }, N)
    ), u = s && !F ? e.createElement(
      "div",
      {
        style: {
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 12px",
          marginBottom: 12,
          background: "#f6ffed",
          border: "1px solid #b7eb8f",
          borderRadius: 6
        }
      },
      e.createElement(pe, { size: "small" }),
      e.createElement(
        D,
        { style: { fontSize: 12, color: "#52c41a" } },
        `正在连接 ${j}...`
      )
    ) : null, $ = s && F ? e.createElement(
      "div",
      {
        style: {
          background: "#e6f4ff",
          border: "1px solid #91caff",
          borderRadius: 6,
          padding: "8px 12px",
          marginBottom: 12
        }
      },
      e.createElement(
        D,
        { style: { fontSize: 12, color: "#1677ff" } },
        `实时进度 (已接收 ${te} 个事件):`
      )
    ) : null, me = e.createElement(
      "div",
      {
        style: {
          background: "#fafafa",
          border: "1px solid #d9d9d9",
          borderRadius: 6,
          padding: "12px 16px"
        }
      },
      e.createElement(
        D,
        { style: { fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-word" } },
        i
      )
    );
    return e.createElement(
      "div",
      {
        style: {
          width: "100%",
          borderRadius: 10,
          border: "1px solid #f0f0f0",
          overflow: "hidden",
          background: "#fff",
          padding: "12px 16px",
          margin: "4px 0"
        }
      },
      e.createElement("div", { style: { marginBottom: 12 } }, m),
      u,
      $,
      me,
      e.createElement(
        "div",
        {
          style: { fontSize: 11, color: "#8c8c8c", marginTop: 8 }
        },
        `事件数: ${te}`,
        l != null && l.task_id ? ` | 任务ID: ${l.task_id.slice(0, 12)}...` : "",
        l != null && l.context_id ? ` | 会话: ${l.context_id.slice(0, 12)}...` : ""
      )
    );
  }
  const {
    Form: Z,
    Select: he,
    Drawer: st,
    Modal: lt,
    Empty: at,
    Badge: Re,
    Divider: ot,
    message: oe
  } = z, {
    ApiOutlined: xt,
    PlusOutlined: Oe,
    ReloadOutlined: Ee,
    DeleteOutlined: Le,
    LinkOutlined: Be,
    DisconnectOutlined: wt
  } = b || {}, { useEffect: De } = e, xe = "/a2a/agents";
  function Ce() {
    var t;
    try {
      const n = sessionStorage.getItem("qwenpaw-agent-storage") || localStorage.getItem("qwenpaw-agent-storage");
      if (n) {
        const s = JSON.parse(n);
        return ((t = s == null ? void 0 : s.state) == null ? void 0 : t.selectedAgent) || null;
      }
    } catch {
    }
    return null;
  }
  async function we(t, n) {
    const s = L(t), a = H == null ? void 0 : H(), f = Ce(), p = {
      "Content-Type": "application/json",
      ...a ? { Authorization: `Bearer ${a}` } : {},
      ...f ? { "X-Agent-Id": f } : {}
    }, l = await fetch(s, { ...n, headers: { ...p, ...(n == null ? void 0 : n.headers) || {} } });
    if (!l.ok) {
      const r = await l.text().catch(() => "");
      throw new Error(r || `HTTP ${l.status}`);
    }
    return l.status === 204 || l.headers.get("content-length") === "0" ? null : l.json();
  }
  function it(t) {
    var r;
    const { agent: n, onClick: s } = t, a = n.status === "connected", f = a ? "#52c41a" : n.status === "error" ? "#ff4d4f" : "#d9d9d9", p = a ? "已连接" : n.status === "error" ? "错误" : "未连接", l = {
      gateway: "阿里云Agent Hub",
      bearer: "Bearer Token",
      api_key: "API Key"
    };
    return e.createElement(
      B,
      {
        hoverable: !0,
        onClick: s,
        size: "small",
        style: { cursor: "pointer" },
        title: e.createElement(
          A,
          null,
          e.createElement(Re, { color: f }),
          e.createElement("span", null, n.name || n.alias || n.url)
        ),
        extra: n.auth_type ? e.createElement(c, { color: "blue" }, l[n.auth_type] || n.auth_type) : null
      },
      e.createElement(
        "div",
        { style: { fontSize: 12, color: "#666" } },
        e.createElement(
          "div",
          { style: { marginBottom: 4 } },
          Be ? e.createElement(Be, { style: { marginRight: 4 } }) : null,
          n.url
        ),
        n.description ? e.createElement("div", { style: { marginBottom: 4, color: "#999" } }, n.description) : null,
        ((r = n.skills) == null ? void 0 : r.length) > 0 ? e.createElement(
          "div",
          null,
          n.skills.slice(0, 3).map(
            (P, j) => e.createElement(c, { key: j, style: { fontSize: 11 } }, P.name)
          ),
          n.skills.length > 3 ? e.createElement(c, { style: { fontSize: 11 } }, `+${n.skills.length - 3}`) : null
        ) : null,
        e.createElement(
          "div",
          { style: { marginTop: 4, color: f, fontSize: 11 } },
          p,
          n.error ? ` - ${n.error}` : ""
        )
      )
    );
  }
  function ct() {
    const t = e.useRef(Ce()), [n, s] = C(t.current);
    return De(() => {
      const a = () => {
        const p = Ce();
        p !== t.current && (t.current = p, s(p));
      }, f = setInterval(a, 200);
      return window.addEventListener("storage", a), () => {
        clearInterval(f), window.removeEventListener("storage", a);
      };
    }, []), n;
  }
  function ut() {
    var R, Q;
    const t = ct(), [n, s] = C([]), [a, f] = C(!0), [p, l] = C(!1), [r, P] = C(null), [j, F] = C(!1), [U, M] = C(!1), [te, J] = C(!1), [k] = Z.useForm(), v = V(async () => {
      f(!0);
      try {
        const o = await we(xe);
        s((o == null ? void 0 : o.agents) || []);
      } catch {
        s([]);
      } finally {
        f(!1);
      }
    }, []);
    De(() => {
      v();
    }, [t]);
    const N = V(() => {
      F(!0), P(null), l(!0), k.resetFields(), k.setFieldsValue({ url: "", alias: "", auth_type: "", auth_token: "" });
    }, [k]), i = V((o) => {
      F(!1), P(o), l(!0);
    }, []), m = V(() => {
      l(!1), P(null), F(!1), k.resetFields();
    }, [k]), u = V(async () => {
      let o;
      try {
        o = await k.validateFields();
      } catch {
        return;
      }
      const g = {
        url: String(o.url || "").trim(),
        alias: String(o.alias || "").trim() || void 0,
        auth_type: String(o.auth_type || ""),
        auth_token: String(o.auth_token || "")
      };
      if (g.url) {
        M(!0);
        try {
          await we(xe, { method: "POST", body: JSON.stringify(g) }), oe.success("A2A Agent 注册成功"), await v(), m();
        } catch (G) {
          oe.error(G.message || "注册失败");
        } finally {
          M(!1);
        }
      }
    }, [k, v, m]), $ = V(async () => {
      if (!r) return;
      const o = r.alias || r.url;
      lt.confirm({
        title: `删除 ${o}`,
        content: "确定删除该远程 A2A Agent 吗？此操作不可撤销。",
        okText: "删除",
        cancelText: "取消",
        okButtonProps: { danger: !0 },
        async onOk() {
          try {
            await we(`${xe}/${encodeURIComponent(o)}`, { method: "DELETE" }), oe.success("A2A Agent 已删除"), await v(), m();
          } catch (g) {
            oe.error(g.message || "删除失败");
          }
        }
      });
    }, [r, v, m]), me = V(async () => {
      if (!r) return;
      const o = r.alias || r.url;
      J(!0);
      try {
        const g = await we(`${xe}/${encodeURIComponent(o)}/refresh`, {
          method: "POST"
        });
        oe.success("Agent Card 已刷新"), await v(), g && P(g);
      } catch (g) {
        oe.error(g.message || "刷新失败");
      } finally {
        J(!1);
      }
    }, [r, v]), ne = ((R = Z.useWatch) == null ? void 0 : R.call(Z, "auth_type", k)) ?? "", ie = e.createElement(
      Z,
      { form: k, layout: "vertical" },
      e.createElement(
        Z.Item,
        { name: "url", label: "Agent URL", rules: [{ required: !0, message: "请输入 Agent URL" }] },
        e.createElement(S, { placeholder: "https://agent.example.com" })
      ),
      e.createElement(
        Z.Item,
        { name: "alias", label: "别名" },
        e.createElement(S, { placeholder: "输入别名（可选）" })
      ),
      e.createElement(
        Z.Item,
        { name: "auth_type", label: "认证类型" },
        e.createElement(
          he,
          { allowClear: !0, placeholder: "无认证" },
          e.createElement(he.Option, { value: "bearer" }, "Bearer Token"),
          e.createElement(he.Option, { value: "api_key" }, "API Key"),
          e.createElement(he.Option, { value: "gateway" }, "阿里云Agent Hub")
        )
      ),
      ne === "gateway" ? e.createElement(
        "div",
        { style: { marginBottom: 16, padding: "8px 12px", background: "#f6ffed", border: "1px solid #b7eb8f", borderRadius: 6, fontSize: 12, color: "#52c41a" } },
        "阿里云Agent Hub 模式将自动使用环境变量中的 AK-SK 换取 Bearer Token"
      ) : null,
      ne && ne !== "gateway" ? e.createElement(
        Z.Item,
        { name: "auth_token", label: "认证凭证" },
        e.createElement(S.Password, { placeholder: "Bearer Token 或 API Key" })
      ) : null
    ), ce = r ? e.createElement(
      "div",
      null,
      e.createElement(
        Y,
        { column: 1, bordered: !0, size: "small" },
        e.createElement(Y.Item, { label: "URL" }, r.url),
        e.createElement(Y.Item, { label: "别名" }, r.alias || "-"),
        e.createElement(Y.Item, { label: "Agent 名称" }, r.name || "-"),
        e.createElement(
          Y.Item,
          { label: "状态" },
          e.createElement(Re, {
            color: r.status === "connected" ? "#52c41a" : r.status === "error" ? "#ff4d4f" : "#d9d9d9",
            text: r.status === "connected" ? "已连接" : r.status === "error" ? "错误" : "未连接"
          })
        ),
        e.createElement(
          Y.Item,
          { label: "认证类型" },
          r.auth_type ? e.createElement(
            c,
            { color: "blue" },
            { gateway: "阿里云Agent Hub", bearer: "Bearer Token", api_key: "API Key" }[r.auth_type] || r.auth_type
          ) : "无认证"
        ),
        e.createElement(Y.Item, { label: "描述" }, r.description || "-"),
        e.createElement(Y.Item, { label: "版本" }, r.version || "-")
      ),
      ((Q = r.skills) == null ? void 0 : Q.length) > 0 ? e.createElement(
        "div",
        { style: { marginTop: 16 } },
        e.createElement("h4", null, "技能"),
        ...r.skills.map(
          (o, g) => e.createElement(
            B,
            { key: g, size: "small", style: { marginBottom: 8 } },
            e.createElement("strong", null, o.name),
            o.description ? e.createElement("div", { style: { color: "#666", fontSize: 12 } }, o.description) : null
          )
        )
      ) : null,
      r.capabilities ? e.createElement(
        "div",
        { style: { marginTop: 16 } },
        e.createElement("h4", null, "能力"),
        e.createElement(
          A,
          null,
          e.createElement(c, { color: r.capabilities.streaming ? "green" : "default" }, "Streaming"),
          e.createElement(c, { color: r.capabilities.push_notifications ? "green" : "default" }, "Push Notifications")
        )
      ) : null,
      r.error ? e.createElement(
        "div",
        { style: { marginTop: 16, padding: "8px 12px", background: "#fff2f0", border: "1px solid #ffccc7", borderRadius: 6, fontSize: 12, color: "#ff4d4f" } },
        r.error
      ) : null,
      e.createElement(ot, null),
      e.createElement(
        A,
        null,
        e.createElement(
          x,
          {
            type: "primary",
            icon: Ee ? e.createElement(Ee) : null,
            loading: te,
            onClick: me
          },
          "刷新 Agent Card"
        ),
        e.createElement(
          x,
          {
            danger: !0,
            icon: Le ? e.createElement(Le) : null,
            onClick: $
          },
          "删除"
        )
      )
    ) : null, W = e.createElement(
      st,
      {
        title: j ? "注册远程 A2A Agent" : (r == null ? void 0 : r.name) || (r == null ? void 0 : r.alias) || "Agent 详情",
        open: p,
        onClose: m,
        width: 480,
        footer: j ? e.createElement(
          A,
          { style: { float: "right" } },
          e.createElement(x, { onClick: m }, "取消"),
          e.createElement(x, { type: "primary", loading: U, onClick: u }, "注册")
        ) : null
      },
      j ? ie : ce
    ), K = e.createElement(
      "div",
      { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 } },
      e.createElement("h2", { style: { margin: 0 } }, "A2A 远程 Agent"),
      e.createElement(
        A,
        null,
        e.createElement(
          x,
          { icon: Ee ? e.createElement(Ee) : null, onClick: v, loading: a },
          "刷新列表"
        ),
        e.createElement(
          x,
          {
            type: "primary",
            icon: Oe ? e.createElement(Oe) : null,
            onClick: N
          },
          "注册 Agent"
        )
      )
    ), q = a ? e.createElement(
      "div",
      { style: { textAlign: "center", padding: 60 } },
      e.createElement(pe, { size: "large" })
    ) : n.length === 0 ? e.createElement(at, { description: "暂无注册的远程 A2A Agent" }) : e.createElement(
      "div",
      {
        style: {
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 12
        }
      },
      ...n.map(
        (o) => e.createElement(it, {
          key: o.alias || o.url,
          agent: o,
          onClick: () => i(o)
        })
      )
    );
    return e.createElement(
      "div",
      { style: { padding: 24 } },
      K,
      q,
      W
    );
  }
  (Me = (je = window.QwenPaw).registerToolRender) == null || Me.call(je, "cloudpaw", {
    proposal_choice: tt,
    manage_prd: nt,
    a2a_call: rt
  }), (He = (Ne = window.QwenPaw).registerRoutes) == null || He.call(Ne, "cloudpaw", [
    {
      path: "/a2a",
      component: ut,
      label: "A2A",
      icon: "🔗",
      priority: 10
    }
  ]), gt(), yt(), pt();
}
function pt() {
  const e = window.QwenPaw, { getApiUrl: z } = e.host, b = (c, d) => `[A2A_DIRECT_CALL] 用户通过 /${c} 指定了远程 A2A Agent。请立即使用 a2a_call 工具将以下问题原样转发给 agent 别名 "${c}"，不要自己回答、不要修改内容、不要添加额外解释。用户原始问题如下：
---
${d}
---
请仅使用 a2a_call(agent_alias="${c}", message="上述用户原始问题") 来转发，然后将远程 agent 的回复结果返回给用户。`;
  function L(c) {
    const d = c.match(/^\/([\w.-]+)\s+(.+)$/s);
    return d ? { alias: d[1], cleanMsg: d[2] } : null;
  }
  function H(c) {
    if (typeof c == "string") {
      const d = L(c.trim());
      return d && d.cleanMsg ? b(d.alias, d.cleanMsg) : c;
    }
    return Array.isArray(c) ? c.map((d) => {
      if (d.type === "text" && typeof d.text == "string") {
        const A = L(d.text.trim());
        if (A && A.cleanMsg)
          return { ...d, text: b(A.alias, A.cleanMsg) };
      }
      return d;
    }) : c;
  }
  const B = z("/console/chat"), le = window.fetch.bind(window);
  window.fetch = async function(c, d) {
    if ((typeof c == "string" ? c : c instanceof Request ? c.url : String(c)) === B && (d != null && d.body))
      try {
        const x = JSON.parse(d.body);
        x.input && Array.isArray(x.input) && (x.input = x.input.map((S) => S.role === "user" && S.content ? { ...S, content: H(S.content) } : S), d = { ...d, body: JSON.stringify(x) });
      } catch {
      }
    return le(c, d);
  }, console.info("[cloudpaw] / A2A slash command system-hint injection initialized");
}
function gt() {
  const e = "qwenpaw-last-used-agent", z = "qwenpaw-agent-storage", b = "cloudpaw-first-install", L = "cloud-orchestrator";
  if (!localStorage.getItem(b)) {
    localStorage.setItem(b, "true"), localStorage.setItem(e, L);
    try {
      const H = localStorage.getItem(z);
      if (H) {
        const B = JSON.parse(H);
        B.state = B.state || {}, B.state.selectedAgent = L, localStorage.setItem(z, JSON.stringify(B));
      } else
        localStorage.setItem(z, JSON.stringify({
          version: 0,
          state: {
            selectedAgent: L,
            agents: [],
            lastChatIdByAgent: {}
          }
        }));
    } catch {
    }
    try {
      sessionStorage.setItem(z, JSON.stringify({
        version: 0,
        state: {
          selectedAgent: L,
          agents: [],
          lastChatIdByAgent: {}
        }
      }));
    } catch {
    }
    console.info("[cloudpaw] Set default agent to cloud-orchestrator for first-time user"), window.location.reload();
  }
}
function yt() {
  var A;
  const e = (A = window.QwenPaw) == null ? void 0 : A.modules;
  if (!e) return;
  const z = e["Chat/OptionsPanel/defaultConfig"];
  if (!(z != null && z.configProvider)) {
    console.warn("[cloudpaw] configProvider not found — skipping welcome/theme patch");
    return;
  }
  const b = z.configProvider, L = b.getConfig.bind(b), H = "https://gw.alicdn.com/imgextra/i2/O1CN01pyXzjQ1EL1PuZMlSd_!!6000000000334-2-tps-288-288.png", B = {
    zh: "Hi, 我是 CloudPaw",
    en: "Hi, I'm CloudPaw",
    ja: "こんにちは、CloudPaw です",
    ru: "Привет, я CloudPaw"
  }, le = {
    zh: "我可以帮助你部署云资源、管理基础设施，并在阿里云上编排服务。请在左上角下拉框选择「CloudPaw-Master」开启任务。对于复杂的长程任务，建议使用 /mission 命令启动 Mission Mode 来自动拆解和执行。",
    en: "I can help you deploy cloud resources, manage infrastructure, and orchestrate services on Alibaba Cloud. Please select 'CloudPaw-Master' from the dropdown in the top-left corner to get started. For complex, multi-step tasks, use /mission to start Mission Mode for automated decomposition and execution.",
    ja: "クラウドリソースのデプロイ、インフラの管理、Alibaba Cloudでのサービスオーケストレーションをお手伝いします。左上のドロップダウンから「CloudPaw-Master」を選択してタスクを開始してください。複雑なタスクには /mission コマンドで Mission Mode を起動し、自動分解・実行できます。",
    ru: "Я могу помочь вам развернуть облачные ресурсы и управлять инфраструктурой на Alibaba Cloud. Выберите 'CloudPaw-Master' в выпадающем списке в левом верхнем углу, чтобы начать. Для сложных задач используйте /mission для автоматической декомпозиции и выполнения."
  }, c = {
    zh: [
      {
        label: "创建个人主页并部署到云端",
        value: "/mission 帮我创建一个个人主页并上线到云端。页面包含：个人介绍、技能展示、项目经历、联系方式，所有个人信息请先用占位符代替。风格简洁清爽，适配手机和电脑。请使用阿里云 ECS 部署。"
      },
      {
        label: "快速发布 API 服务到云端",
        value: "/mission 帮我把一个 API 服务快速发布到云端。我希望默认提供 /health 和 /hello 两个接口，并给我可直接调用的地址和示例请求，配置尽量简单清晰。"
      }
    ],
    en: [
      {
        label: "Create a personal homepage and deploy to the cloud",
        value: "/mission Help me create a personal homepage and deploy it to the cloud. The page should include: personal introduction, skills, project experience, and contact info — please use placeholders for all personal information. The style should be clean and minimal, responsive for mobile and desktop. Please deploy using Alibaba Cloud ECS."
      },
      {
        label: "Deploy an API service to the cloud",
        value: "/mission Help me quickly deploy an API service to the cloud. I want it to provide /health and /hello endpoints by default, and give me a callable URL with example requests. Keep the configuration as simple and clean as possible."
      }
    ]
  };
  function d() {
    const x = localStorage.getItem("language") || "";
    return x ? x.split("-")[0] : (navigator.language || "").split("-")[0] || "en";
  }
  b.getGreeting = () => B[d()] || B.en, b.getDescription = () => le[d()] || le.en, b.getPrompts = () => c[d()] || c.en, b.getConfig = function(x) {
    var fe;
    const S = L(x);
    return {
      ...S,
      theme: {
        ...S.theme,
        leftHeader: {
          ...(fe = S.theme) == null ? void 0 : fe.leftHeader,
          title: "Work with CloudPaw"
        }
      },
      welcome: {
        ...S.welcome,
        avatar: H
      }
    };
  }, console.info("[cloudpaw] Patched welcome config & theme via configProvider");
}
mt();
