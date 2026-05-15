function xt() {
  var Fe, Ke, qe, Xe;
  const { React: e, antd: M, antdIcons: J, getApiUrl: K, getApiToken: Q } = window.QwenPaw.host, {
    Card: W,
    Table: $,
    Tag: B,
    Typography: fe,
    Space: q,
    Button: P,
    Input: Y,
    Radio: me,
    Collapse: kt,
    Descriptions: V,
    Tooltip: Oe,
    Spin: Te,
    message: ze
  } = M, { Text: U } = fe, { TextArea: Ye } = Y, { useState: O, useMemo: Ee, useCallback: Z, useRef: Ct } = e, {
    InfoCircleOutlined: Se,
    DownOutlined: Ne,
    RightOutlined: Ge,
    CheckCircleOutlined: we,
    FieldTimeOutlined: xe,
    FileTextOutlined: $e
  } = J || {};
  function Me(t) {
    var a, l;
    const n = (l = (a = t == null ? void 0 : t.content) == null ? void 0 : a[0]) == null ? void 0 : l.data, o = n == null ? void 0 : n.arguments;
    if (typeof o == "string")
      try {
        return JSON.parse(o);
      } catch {
        return {};
      }
    return o ?? {};
  }
  function Ve() {
    return window.currentSessionId ?? null;
  }
  function ee(t) {
    return typeof t == "string" ? t : t && typeof t == "object" && "text" in t ? t.text : String(t ?? "");
  }
  function Ze(t) {
    if (t == null) return !0;
    const n = ee(t).trim();
    return !!(!n || /^[¥$]?0+(\.0+)?$/.test(n) || /^[-–—]+$/.test(n));
  }
  async function et(t, n) {
    try {
      const o = Q(), a = {
        "Content-Type": "application/json"
      };
      return o && (a.Authorization = `Bearer ${o}`), (await fetch(K("/interaction"), {
        method: "POST",
        headers: a,
        body: JSON.stringify({ session_id: t, result: n })
      })).ok;
    } catch {
      return !1;
    }
  }
  function De(t) {
    if (!t) return null;
    if (typeof t == "string")
      try {
        const n = JSON.parse(t);
        if (Array.isArray(n)) {
          const o = n.find(
            (a) => (a == null ? void 0 : a.type) === "text" && (a == null ? void 0 : a.text)
          );
          return (o == null ? void 0 : o.text) ?? null;
        }
        if (typeof n == "string") return n;
      } catch {
        return t;
      }
    if (Array.isArray(t)) {
      const n = t.find((o) => (o == null ? void 0 : o.type) === "text" && (o == null ? void 0 : o.text));
      return (n == null ? void 0 : n.text) ?? null;
    }
    return null;
  }
  function tt(t) {
    var s, r;
    if (!t || t.length < 2) return null;
    const n = (r = (s = t[1]) == null ? void 0 : s.data) == null ? void 0 : r.output, o = De(n);
    if (!o) return null;
    if (o.startsWith("Error:")) return o;
    const a = o.match(/^用户选择了「(.+?)」并确认部署$/);
    if (a) return `已确认部署「${a[1]}」`;
    const l = o.match(
      /^用户选择「(.+?)」并要求调整[：:](.+)$/
    );
    if (l)
      return `已选择「${l[1]}」并调整：${l[2]}`;
    if (o === "用户确认部署") return "已确认部署";
    const u = o.match(/^用户要求调整资源[：:](.+)$/);
    return u ? `已反馈调整意见：${u[1]}` : "已确认";
  }
  const Le = [
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
  ], nt = new Set(
    Le.map((t) => t.toLowerCase())
  );
  function ve(t) {
    if (!Array.isArray(t) || t.length !== 10) return !1;
    const n = ee(t[0]).trim().toLowerCase();
    return nt.has(n);
  }
  function Be(t) {
    if (!Array.isArray(t) || t.length !== 10) return !1;
    const n = ee(t[0]).trim();
    return /^(合计|总计|total)/i.test(n);
  }
  function rt(t) {
    const n = [];
    let o = [];
    for (const a of t)
      o.push(a), Be(a) && (n.push(o), o = []);
    return o.length > 0 && (n.length > 0 ? n[n.length - 1].push(...o) : n.push(o)), n.length > 0 ? n : [t];
  }
  function ot(t) {
    return typeof t == "string" ? t : t && typeof t == "object" && t.text ? t.url ? e.createElement(
      "a",
      {
        href: t.url,
        target: "_blank",
        rel: "noopener noreferrer"
      },
      t.text
    ) : t.text : String(t ?? "");
  }
  function st({ data: t }) {
    var H, he, ce;
    const [n, o] = O("confirm"), [a, l] = O(""), [u, s] = O(!1), [r, g] = O(null), [A, h] = O(
      {}
    ), z = e.useRef(!1), D = e.useRef(null), [, p] = O(0), C = t == null ? void 0 : t.content, E = C && C.length >= 2 && ((he = (H = C[1]) == null ? void 0 : H.data) == null ? void 0 : he.output), S = Ee(
      () => tt(C),
      [C]
    ), N = z.current || E || S !== null, i = Ee(() => {
      const x = Me(t), y = x == null ? void 0 : x.data;
      if (!y) return null;
      try {
        const f = typeof y == "string" ? JSON.parse(y) : y;
        let v;
        if (x.strategy_names)
          try {
            const _ = typeof x.strategy_names == "string" ? JSON.parse(x.strategy_names) : x.strategy_names;
            v = Array.isArray(_) ? _ : [];
          } catch {
            v = [];
          }
        else f != null && f.proposal_names ? v = f.proposal_names : v = [];
        const G = v.length >= 2 ? v.length : 0;
        let k;
        if (Array.isArray(f) && f.length > 0)
          if (Array.isArray(f[0]) && f[0].length === 10 && !Array.isArray(f[0][0])) {
            const I = f.filter(
              (R) => !ve(R)
            );
            if (I.filter(
              (R) => Be(R)
            ).length >= 2)
              k = rt(I);
            else if (G >= 2 && I.length >= G * 2) {
              const R = Math.ceil(I.length / G);
              k = [];
              for (let ue = 0; ue < I.length; ue += R)
                k.push(I.slice(ue, ue + R));
            } else
              k = [I];
          } else
            k = f.map(
              (I) => I.filter(
                (ne) => Array.isArray(ne) && ne.length === 10 && !ve(ne)
              )
            );
        else if (f != null && f.proposals)
          k = f.proposals.map(
            (_) => _.filter((I) => !ve(I))
          );
        else
          return null;
        if (k = k.filter((_) => _.length > 0), k.length === 0) return null;
        const de = ["方案一", "方案二", "方案三", "方案四", "方案五"];
        if (v.length < k.length)
          for (let _ = v.length; _ < k.length; _++)
            v.push(de[_] || `方案${_ + 1}`);
        return { proposals: k, names: v };
      } catch {
        return null;
      }
    }, [t]), d = Ve(), m = (((ce = i == null ? void 0 : i.proposals) == null ? void 0 : ce.length) ?? 0) > 1, L = Z(async () => {
      if (!d || N || !i) return;
      const x = m ? r : 0, y = i.names[x ?? 0] || `方案${(x ?? 0) + 1}`;
      let f;
      n === "confirm" ? f = `用户选择了「${y}」并确认部署` : f = `用户选择「${y}」并要求调整：${a.trim() || "未填写具体要求"}`, s(!0);
      const v = await et(d, f);
      s(!1), v ? (z.current = !0, n === "confirm" ? D.current = `已确认部署「${y}」` : D.current = `已选择「${y}」并调整：${a.trim()}`, p((G) => G + 1), ze.success(
        n === "confirm" ? "已确认部署方案" : "已提交调整意见"
      )) : ze.error("操作失败，请重试");
    }, [
      d,
      N,
      i,
      n,
      a,
      r,
      m
    ]), ge = (t == null ? void 0 : t.status) === "in_progress" || (t == null ? void 0 : t.status) === "created";
    if (!i)
      return ge ? e.createElement(
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
        e.createElement(Te, { size: "default" }),
        e.createElement(
          U,
          { type: "secondary", style: { fontSize: 13 } },
          "正在生成资源方案..."
        )
      ) : e.createElement(
        W,
        { size: "small", style: { margin: "4px 0" } },
        e.createElement(U, { type: "secondary" }, "无法解析方案数据")
      );
    const { proposals: oe, names: ye } = i, ie = Le.map((x, y) => ({
      title: x,
      dataIndex: `col_${y}`,
      key: `col_${y}`,
      render: (f) => ot(f),
      ellipsis: y < 3
    }));
    let se = "待确认", ae = "processing";
    N && (ae = "success", se = D.current || S || "已确认");
    const X = e.createElement(
      B,
      {
        color: ae,
        style: { marginLeft: 4 }
      },
      se
    ), F = e.createElement(
      q,
      { size: 8 },
      e.createElement("span", null, "☁️"),
      e.createElement(
        U,
        { strong: !0, style: { fontSize: 14 } },
        N ? "资源配置方案" : "请确认您的资源配置方案"
      ),
      X
    ), j = oe.map((x, y) => {
      const f = m ? r === y : !0, v = A[y] || !1, G = (b) => {
        const re = ee(b[0] || "").trim();
        return /^合计|^总计|^total/i.test(re);
      }, k = x.find(G), de = x.filter((b) => !G(b)), _ = de.map((b) => ({
        type: ee(b[0] || ""),
        purpose: ee(b[1] || ""),
        spec: ee(b[2] || ""),
        cost: b[9] ?? null
      })), I = k ? ee(k[9] ?? "") : "", ne = x.map((b, re) => {
        const Qe = { key: re };
        return b.forEach((St, wt) => {
          Qe[`col_${wt}`] = St;
        }), Qe;
      }), R = f ? "2px solid #1677ff" : "1px solid #e8e8e8", ue = f ? "0 0 0 2px #e6f4ff" : "none";
      return e.createElement(
        "div",
        {
          key: y,
          style: {
            flex: 1,
            minWidth: 240,
            border: R,
            borderRadius: 8,
            cursor: m ? "pointer" : "default",
            transition: "all 0.2s ease",
            boxShadow: ue,
            background: "#fff"
          },
          onClick: m ? () => g(y) : void 0
        },
        e.createElement(
          "div",
          { style: { padding: "10px 12px" } },
          // Proposal name
          e.createElement(
            U,
            {
              strong: !0,
              style: { fontSize: 14, display: "block", marginBottom: 8 }
            },
            ye[y]
          ),
          ..._.map(
            (b, re) => e.createElement(
              "div",
              {
                key: re,
                style: {
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "4px 0",
                  borderBottom: re < _.length - 1 ? "1px solid #f5f5f5" : "none"
                }
              },
              e.createElement(
                "div",
                { style: { flex: 1, minWidth: 0 } },
                e.createElement(
                  "span",
                  { style: { fontSize: 12, color: "#262626" } },
                  b.type
                ),
                b.spec && e.createElement(
                  "span",
                  {
                    style: { fontSize: 11, color: "#8c8c8c", marginLeft: 6 }
                  },
                  b.spec
                )
              ),
              !Ze(b.cost) && e.createElement(
                "span",
                {
                  style: {
                    fontSize: 12,
                    color: "#595959",
                    flexShrink: 0,
                    marginLeft: 8
                  }
                },
                ee(b.cost)
              )
            )
          ),
          // Total cost
          I && e.createElement(
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
            e.createElement(
              "span",
              { style: { fontSize: 12, fontWeight: 500 } },
              "合计"
            ),
            e.createElement(
              "span",
              {
                style: { fontSize: 14, fontWeight: 700, color: "#fa541c" }
              },
              I
            )
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
              onClick: (b) => {
                b.stopPropagation(), h((re) => ({
                  ...re,
                  [y]: !re[y]
                }));
              }
            },
            e.createElement(
              v && Ne ? Ne : Ge || "span",
              {
                style: { fontSize: 10 }
              }
            ),
            e.createElement(
              "span",
              null,
              `明细 · ${de.length} 项`
            )
          ),
          v && e.createElement(
            "div",
            {
              onClick: (b) => b.stopPropagation(),
              style: { marginTop: 4, maxHeight: 260, overflow: "auto" }
            },
            e.createElement($, {
              columns: ie,
              dataSource: ne,
              pagination: !1,
              size: "small",
              scroll: { x: "max-content" }
            })
          )
        )
      );
    }), c = e.createElement(
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
      Se ? e.createElement(Se, {
        style: {
          color: "#faad14",
          fontSize: 14,
          flexShrink: 0,
          marginTop: 1
        }
      }) : e.createElement("span", null, "⚠️"),
      e.createElement(
        "span",
        {
          style: { fontSize: 12, color: "#8c6e00", lineHeight: 1.5 }
        },
        "在服务部署与配置过程中，可能因实际资源需求变化导致资源变配及费用调整，请及时关注实际资源使用情况与账单详情。"
      )
    ), w = !N && d && !(m && r === null) && e.createElement(
      "div",
      null,
      e.createElement(
        "div",
        {
          style: {
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            marginBottom: 8
          }
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
            onClick: () => o("confirm")
          },
          e.createElement(me, { checked: n === "confirm" }),
          e.createElement(
            "span",
            { style: { fontSize: 13 } },
            "确认部署"
          )
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
              style: {
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer"
              },
              onClick: () => o("adjust")
            },
            e.createElement(me, { checked: n === "adjust" }),
            e.createElement(
              "span",
              { style: { fontSize: 13 } },
              "调整资源"
            )
          ),
          n === "adjust" && e.createElement(Ye, {
            value: a,
            onChange: (x) => l(x.target.value),
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
          U,
          { type: "secondary", style: { fontSize: 11 } },
          m ? "一小时后未操作将自动选择第一个方案" : "一小时后未操作将自动确认部署"
        ),
        e.createElement(
          P,
          {
            type: "primary",
            size: "small",
            loading: u,
            onClick: L,
            disabled: n === "adjust" && !a.trim()
          },
          n === "confirm" ? "确认部署" : "提交调整"
        )
      )
    ), T = m && r === null && !N && e.createElement(
      "div",
      {
        style: {
          textAlign: "center",
          padding: "8px 0 4px",
          color: "rgba(0,0,0,0.45)",
          fontSize: 12
        }
      },
      "请点击选择一个方案后继续操作"
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
      // Header
      e.createElement("div", { style: { marginBottom: 10 } }, F),
      // Proposals grid
      e.createElement(
        "div",
        {
          style: {
            display: "flex",
            gap: 10,
            marginBottom: 12,
            flexWrap: "wrap"
          }
        },
        ...j
      ),
      T,
      c,
      !N && w
    );
  }
  function at({ data: t }) {
    const [n, o] = O(null), [a, l] = O(!1), u = (t == null ? void 0 : t.status) === "in_progress" || (t == null ? void 0 : t.status) === "created", s = Ee(() => {
      const i = Me(t);
      return (i == null ? void 0 : i.loop_dir) || null;
    }, [t]), r = Ee(() => {
      var d, m, L;
      const i = De((L = (m = (d = t == null ? void 0 : t.content) == null ? void 0 : d[1]) == null ? void 0 : m.data) == null ? void 0 : L.output);
      if (!i) return null;
      try {
        return JSON.parse(i);
      } catch {
        return null;
      }
    }, [t]), g = (r == null ? void 0 : r.status) === "ok", A = (r == null ? void 0 : r.status) === "error", h = A ? (r == null ? void 0 : r.message) || "未知错误" : null, z = Z(async () => {
      if (s)
        try {
          const i = Q(), d = {};
          i && (d.Authorization = `Bearer ${i}`);
          const m = await fetch(
            K(`/prd?loop_dir=${encodeURIComponent(s)}`),
            { headers: d }
          );
          if (!m.ok) {
            l(!0);
            return;
          }
          const L = await m.json();
          L && Array.isArray(L.userStories) ? (o(L), l(!1)) : l(!0);
        } catch {
          l(!0);
        }
    }, [s]);
    if (e.useEffect(() => {
      !u && g && s && z();
    }, [u, g, s, z]), u)
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
        e.createElement(Te, { size: "default" }),
        e.createElement(
          U,
          { type: "secondary", style: { fontSize: 13 } },
          "正在更新 PRD..."
        )
      );
    if (A)
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
          U,
          { type: "danger", style: { fontSize: 13 } },
          `PRD 格式错误，将会修正：${h}`
        )
      );
    if (!g || a || !n) return null;
    const D = n.userStories, p = [...D].sort(
      (i, d) => (i.priority || 99) - (d.priority || 99)
    ), C = D.filter((i) => i.passes).length, E = [
      {
        title: "状态",
        key: "status",
        width: 50,
        align: "center",
        render: (i, d) => {
          if (d.passes) {
            const L = we ? e.createElement(we, {
              style: { color: "#52c41a", fontSize: 18 }
            }) : "✅";
            return e.createElement(Oe, { title: "已完成" }, L);
          }
          const m = xe ? e.createElement(xe, {
            style: { color: "#faad14", fontSize: 18 }
          }) : "🕐";
          return e.createElement(Oe, { title: "待处理" }, m);
        }
      },
      {
        title: "ID",
        dataIndex: "id",
        key: "id",
        width: 85,
        render: (i) => e.createElement(B, { color: "blue" }, i)
      },
      {
        title: "标题",
        dataIndex: "title",
        key: "title",
        render: (i) => e.createElement(U, { strong: !0 }, i)
      },
      {
        title: "优先级",
        key: "priority",
        width: 70,
        render: (i, d) => {
          const m = d.priority;
          return e.createElement(
            B,
            { color: "default" },
            m != null ? String(m) : "-"
          );
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
        render: (i, d) => {
          const m = d.acceptanceCriteria;
          return typeof m == "string" ? e.createElement(
            "div",
            {
              style: { fontSize: 12, color: "#666", whiteSpace: "pre-wrap" }
            },
            m.length > 100 ? m.slice(0, 100) + "..." : m
          ) : Array.isArray(m) ? e.createElement(
            "div",
            { style: { fontSize: 12, color: "#666" } },
            m.length > 2 ? m.slice(0, 2).join(", ") + "..." : m.join(", ")
          ) : "-";
        }
      }
    ], S = e.createElement(
      q,
      { size: 8 },
      $e ? e.createElement($e, { style: { color: "#1677ff" } }) : null,
      e.createElement(
        "span",
        { style: { fontSize: 14 } },
        e.createElement(U, { strong: !0 }, n.project || "PRD")
      )
    ), N = e.createElement($, {
      columns: E,
      dataSource: p.map((i) => ({ ...i, key: i.id })),
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
      e.createElement("div", { style: { marginBottom: 8 } }, S),
      e.createElement(V, {
        size: "small",
        column: { xs: 1, sm: 2, md: 3 },
        style: { marginBottom: 12 },
        bordered: !1,
        items: [
          {
            key: "progress",
            label: "进度",
            children: `${C}/${D.length} 完成`
          }
        ]
      }),
      N,
      e.createElement(
        "div",
        {
          style: {
            fontSize: 11,
            color: "#8c8c8c",
            display: "flex",
            alignItems: "center",
            gap: 8
          }
        },
        we ? e.createElement(we, {
          style: { color: "#52c41a", fontSize: 14 }
        }) : "✅",
        e.createElement("span", null, "已完成"),
        e.createElement("span", { style: { margin: "0 4px" } }, "·"),
        xe ? e.createElement(xe, {
          style: { color: "#faad14", fontSize: 14 }
        }) : "🕐",
        e.createElement("span", null, "待处理")
      )
    );
  }
  function lt({ data: t }) {
    var ie, se, ae;
    const n = (t == null ? void 0 : t.status) || "", o = n === "in_progress" || n === "created", a = n === "completed" || n === "canceled" || n === "failed", [l, u] = e.useState(""), [s, r] = e.useState(0), g = e.useRef("");
    e.useEffect(() => {
      var x, y;
      if (!o) return;
      console.log("[a2a] SSE effect triggered, isLoading=true"), u(""), r(0), g.current = "";
      const X = window.QwenPaw, { getApiUrl: F, getApiToken: j } = X.host, c = F("/a2a/call/stream"), w = j();
      console.log("[a2a] SSE URL:", c);
      let T = "";
      try {
        const f = sessionStorage.getItem("qwenpaw-agent-storage") || localStorage.getItem("qwenpaw-agent-storage");
        T = ((y = (x = JSON.parse(f || "{}")) == null ? void 0 : x.state) == null ? void 0 : y.selectedAgent) || "";
      } catch {
      }
      const H = { Accept: "text/event-stream" };
      w && (H.Authorization = `Bearer ${w}`), T && (H["X-Agent-Id"] = T);
      const he = new AbortController();
      let ce = !1;
      return (async () => {
        try {
          console.log("[a2a] Starting SSE fetch...");
          const f = await fetch(c, { headers: H, signal: he.signal });
          if (console.log("[a2a] SSE response status:", f.status), !f.body) {
            console.error("[a2a] No response body");
            return;
          }
          const v = f.body.getReader(), G = new TextDecoder();
          let k = "";
          for (; !ce; ) {
            const { done: de, value: _ } = await v.read();
            if (de) {
              console.log("[a2a] SSE stream ended");
              break;
            }
            k += G.decode(_, { stream: !0 });
            const I = k.split(`
`);
            k = I.pop() ?? "";
            for (const ne of I)
              if (ne.startsWith("data: "))
                try {
                  const R = JSON.parse(ne.slice(6));
                  if (R.done) {
                    console.log("[a2a] SSE done signal received"), ce = !0;
                    break;
                  }
                  typeof R.response_text == "string" && (g.current = R.response_text, u(R.response_text), r(R.event_count ?? 0), console.log(
                    "[a2a] SSE update: text_len=" + R.response_text.length
                  ));
                } catch (R) {
                  console.warn("[a2a] SSE parse error:", R);
                }
          }
        } catch (f) {
          (f == null ? void 0 : f.name) !== "AbortError" && console.error("[a2a stream]", f);
        }
      })(), () => {
        ce = !0, he.abort();
      };
    }, [o]);
    const A = e.useMemo(() => {
      var F, j, c;
      const X = (c = (j = (F = t == null ? void 0 : t.content) == null ? void 0 : F[0]) == null ? void 0 : j.data) == null ? void 0 : c.arguments;
      if (!X) return null;
      try {
        return JSON.parse(X);
      } catch {
        return null;
      }
    }, [(ae = (se = (ie = t == null ? void 0 : t.content) == null ? void 0 : ie[0]) == null ? void 0 : se.data) == null ? void 0 : ae.arguments]), h = (A == null ? void 0 : A.agent_alias) || "", z = (A == null ? void 0 : A.agent_url) || "", D = h || z || "远程 Agent", p = e.useMemo(() => {
      var F;
      if (!a) return null;
      const X = t == null ? void 0 : t.content;
      if (!Array.isArray(X)) return null;
      for (const j of X) {
        const c = (F = j == null ? void 0 : j.data) == null ? void 0 : F.output;
        if (!c) continue;
        let w = "";
        if (Array.isArray(c)) {
          const T = c.find(
            (H) => (H == null ? void 0 : H.type) === "text" && (H == null ? void 0 : H.text)
          );
          w = (T == null ? void 0 : T.text) || "";
        } else if (typeof c == "string")
          try {
            const T = JSON.parse(c);
            if (typeof T == "object" && (T != null && T.response_text)) return T;
          } catch {
            w = c;
          }
        if (w)
          try {
            return JSON.parse(w);
          } catch {
            return { response_text: w, task_state: "completed" };
          }
      }
      return null;
    }, [t == null ? void 0 : t.content, a]), C = ((p == null ? void 0 : p.response_text) || g.current || "").trim() || "等待响应...", E = (p == null ? void 0 : p.error) || "", S = (p == null ? void 0 : p.task_state) || (o ? "working" : "completed"), N = {
      completed: "#52c41a",
      failed: "#ff4d4f",
      error: "#ff4d4f",
      canceled: "#faad14",
      working: "#1677ff"
    }, i = {
      completed: "已完成",
      failed: "失败",
      error: "出错",
      canceled: "已取消",
      working: "执行中"
    }, d = N[S] || "#d9d9d9", m = i[S] || S, L = e.createElement(
      q,
      { size: 8 },
      e.createElement("span", null, "🔗"),
      e.createElement(
        U,
        { strong: !0, style: { fontSize: 14 } },
        `A2A 调用: ${D}`
      ),
      e.createElement(B, { color: d }, m)
    ), ge = o && l ? e.createElement(
      "div",
      {
        style: {
          background: "#f6ffed",
          border: "1px solid #b7eb8f",
          borderRadius: 6,
          padding: "10px 14px",
          marginBottom: 8
        }
      },
      e.createElement(
        U,
        {
          style: {
            fontSize: 12,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            color: "#262626"
          }
        },
        C
      )
    ) : null, oe = !o && C ? e.createElement(
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
        U,
        {
          style: {
            fontSize: 12,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word"
          }
        },
        E ? `错误: ${E}` : C
      )
    ) : null, ye = p || !o && g.current ? e.createElement(
      "div",
      {
        style: {
          fontSize: 11,
          color: "#8c8c8c",
          marginTop: 6
        }
      },
      `事件数: ${(p == null ? void 0 : p.event_count) ?? s}`,
      p != null && p.task_id ? ` | 任务ID: ${p.task_id.slice(0, 12)}...` : "",
      p != null && p.context_id ? ` | 会话: ${p.context_id.slice(0, 12)}...` : ""
    ) : null;
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
      e.createElement("div", { style: { marginBottom: 8 } }, L),
      ge,
      oe,
      ye
    );
  }
  const {
    Form: te,
    Select: Ae,
    Drawer: it,
    Modal: ct,
    Empty: dt,
    Badge: je,
    Divider: ut,
    message: le
  } = M, {
    ApiOutlined: Tt,
    PlusOutlined: He,
    ReloadOutlined: be,
    DeleteOutlined: Je,
    LinkOutlined: We,
    DisconnectOutlined: vt
  } = J || {}, { useEffect: Ue } = e, ke = "/a2a/agents";
  function _e() {
    var t;
    try {
      const n = sessionStorage.getItem("qwenpaw-agent-storage") || localStorage.getItem("qwenpaw-agent-storage");
      if (n) {
        const o = JSON.parse(n);
        return ((t = o == null ? void 0 : o.state) == null ? void 0 : t.selectedAgent) || null;
      }
    } catch {
    }
    return null;
  }
  async function Ce(t, n) {
    const o = K(t), a = Q == null ? void 0 : Q(), l = _e(), u = {
      "Content-Type": "application/json",
      ...a ? { Authorization: `Bearer ${a}` } : {},
      ...l ? { "X-Agent-Id": l } : {}
    }, s = await fetch(o, {
      ...n,
      headers: { ...u, ...(n == null ? void 0 : n.headers) || {} }
    });
    if (!s.ok) {
      const r = await s.text().catch(() => "");
      throw new Error(r || `HTTP ${s.status}`);
    }
    return s.status === 204 || s.headers.get("content-length") === "0" ? null : s.json();
  }
  function ft(t) {
    var r;
    const { agent: n, onClick: o } = t, a = n.status === "connected", l = a ? "#52c41a" : n.status === "error" ? "#ff4d4f" : "#d9d9d9", u = a ? "已连接" : n.status === "error" ? "错误" : "未连接", s = {
      gateway: "阿里云Agent Hub",
      bearer: "Bearer Token",
      api_key: "API Key"
    };
    return e.createElement(
      W,
      {
        hoverable: !0,
        onClick: o,
        size: "small",
        style: { cursor: "pointer" },
        title: e.createElement(
          q,
          null,
          e.createElement(je, { color: l }),
          e.createElement(
            "span",
            null,
            n.name || n.alias || n.url
          )
        ),
        extra: n.auth_type ? e.createElement(
          B,
          { color: "blue" },
          s[n.auth_type] || n.auth_type
        ) : null
      },
      e.createElement(
        "div",
        { style: { fontSize: 12, color: "#666" } },
        e.createElement(
          "div",
          { style: { marginBottom: 4 } },
          We ? e.createElement(We, { style: { marginRight: 4 } }) : null,
          n.url
        ),
        n.description ? e.createElement(
          "div",
          { style: { marginBottom: 4, color: "#999" } },
          n.description
        ) : null,
        ((r = n.skills) == null ? void 0 : r.length) > 0 ? e.createElement(
          "div",
          null,
          n.skills.slice(0, 3).map(
            (g, A) => e.createElement(
              B,
              { key: A, style: { fontSize: 11 } },
              g.name
            )
          ),
          n.skills.length > 3 ? e.createElement(
            B,
            { style: { fontSize: 11 } },
            `+${n.skills.length - 3}`
          ) : null
        ) : null,
        e.createElement(
          "div",
          { style: { marginTop: 4, color: l, fontSize: 11 } },
          u,
          n.error ? ` - ${n.error}` : ""
        )
      )
    );
  }
  function mt() {
    const t = e.useRef(_e()), [n, o] = O(t.current);
    return Ue(() => {
      const a = () => {
        const u = _e();
        u !== t.current && (t.current = u, o(u));
      }, l = setInterval(a, 200);
      return window.addEventListener("storage", a), () => {
        clearInterval(l), window.removeEventListener("storage", a);
      };
    }, []), n;
  }
  function pt() {
    var F, j;
    const t = mt(), [n, o] = O([]), [a, l] = O(!0), [u, s] = O(!1), [r, g] = O(null), [A, h] = O(!1), [z, D] = O(!1), [p, C] = O(!1), [E] = te.useForm(), S = Z(async () => {
      l(!0);
      try {
        const c = await Ce(ke);
        o((c == null ? void 0 : c.agents) || []);
      } catch {
        o([]);
      } finally {
        l(!1);
      }
    }, []);
    Ue(() => {
      S();
    }, [t]);
    const N = Z(() => {
      h(!0), g(null), s(!0), E.resetFields(), E.setFieldsValue({
        url: "",
        alias: "",
        auth_type: "",
        auth_token: ""
      });
    }, [E]), i = Z((c) => {
      h(!1), g(c), s(!0);
    }, []), d = Z(() => {
      s(!1), g(null), h(!1), E.resetFields();
    }, [E]), m = Z(async () => {
      let c;
      try {
        c = await E.validateFields();
      } catch {
        return;
      }
      const w = {
        url: String(c.url || "").trim(),
        alias: String(c.alias || "").trim() || void 0,
        auth_type: String(c.auth_type || ""),
        auth_token: String(c.auth_token || "")
      };
      if (w.url) {
        D(!0);
        try {
          await Ce(ke, {
            method: "POST",
            body: JSON.stringify(w)
          }), le.success("A2A Agent 注册成功"), await S(), d();
        } catch (T) {
          le.error(T.message || "注册失败");
        } finally {
          D(!1);
        }
      }
    }, [E, S, d]), L = Z(async () => {
      if (!r) return;
      const c = r.alias || r.url;
      ct.confirm({
        title: `删除 ${c}`,
        content: "确定删除该远程 A2A Agent 吗？此操作不可撤销。",
        okText: "删除",
        cancelText: "取消",
        okButtonProps: { danger: !0 },
        async onOk() {
          try {
            await Ce(`${ke}/${encodeURIComponent(c)}`, {
              method: "DELETE"
            }), le.success("A2A Agent 已删除"), await S(), d();
          } catch (w) {
            le.error(w.message || "删除失败");
          }
        }
      });
    }, [r, S, d]), ge = Z(async () => {
      if (!r) return;
      const c = r.alias || r.url;
      C(!0);
      try {
        const w = await Ce(
          `${ke}/${encodeURIComponent(c)}/refresh`,
          {
            method: "POST"
          }
        );
        le.success("Agent Card 已刷新"), await S(), w && g(w);
      } catch (w) {
        le.error(w.message || "刷新失败");
      } finally {
        C(!1);
      }
    }, [r, S]), oe = ((F = te.useWatch) == null ? void 0 : F.call(te, "auth_type", E)) ?? "", ye = e.createElement(
      te,
      { form: E, layout: "vertical" },
      e.createElement(
        te.Item,
        {
          name: "url",
          label: "Agent URL",
          rules: [{ required: !0, message: "请输入 Agent URL" }]
        },
        e.createElement(Y, {
          placeholder: "https://agent.example.com"
        })
      ),
      e.createElement(
        te.Item,
        { name: "alias", label: "别名" },
        e.createElement(Y, { placeholder: "输入别名（可选）" })
      ),
      e.createElement(
        te.Item,
        { name: "auth_type", label: "认证类型" },
        e.createElement(
          Ae,
          { allowClear: !0, placeholder: "无认证" },
          e.createElement(
            Ae.Option,
            { value: "bearer" },
            "Bearer Token"
          ),
          e.createElement(Ae.Option, { value: "api_key" }, "API Key"),
          e.createElement(
            Ae.Option,
            { value: "gateway" },
            "阿里云Agent Hub"
          )
        )
      ),
      oe === "gateway" ? e.createElement(
        "div",
        {
          style: {
            marginBottom: 16,
            padding: "8px 12px",
            background: "#f6ffed",
            border: "1px solid #b7eb8f",
            borderRadius: 6,
            fontSize: 12,
            color: "#52c41a"
          }
        },
        "阿里云Agent Hub 模式将自动使用环境变量中的 AK-SK 换取 Bearer Token"
      ) : null,
      oe && oe !== "gateway" ? e.createElement(
        te.Item,
        { name: "auth_token", label: "认证凭证" },
        e.createElement(Y.Password, {
          placeholder: "Bearer Token 或 API Key"
        })
      ) : null
    ), ie = r ? e.createElement(
      "div",
      null,
      e.createElement(
        V,
        { column: 1, bordered: !0, size: "small" },
        e.createElement(
          V.Item,
          { label: "URL" },
          r.url
        ),
        e.createElement(
          V.Item,
          { label: "别名" },
          r.alias || "-"
        ),
        e.createElement(
          V.Item,
          { label: "Agent 名称" },
          r.name || "-"
        ),
        e.createElement(
          V.Item,
          { label: "状态" },
          e.createElement(je, {
            color: r.status === "connected" ? "#52c41a" : r.status === "error" ? "#ff4d4f" : "#d9d9d9",
            text: r.status === "connected" ? "已连接" : r.status === "error" ? "错误" : "未连接"
          })
        ),
        e.createElement(
          V.Item,
          { label: "认证类型" },
          r.auth_type ? e.createElement(
            B,
            { color: "blue" },
            {
              gateway: "阿里云Agent Hub",
              bearer: "Bearer Token",
              api_key: "API Key"
            }[r.auth_type] || r.auth_type
          ) : "无认证"
        ),
        e.createElement(
          V.Item,
          { label: "描述" },
          r.description || "-"
        ),
        e.createElement(
          V.Item,
          { label: "版本" },
          r.version || "-"
        )
      ),
      ((j = r.skills) == null ? void 0 : j.length) > 0 ? e.createElement(
        "div",
        { style: { marginTop: 16 } },
        e.createElement("h4", null, "技能"),
        ...r.skills.map(
          (c, w) => e.createElement(
            W,
            { key: w, size: "small", style: { marginBottom: 8 } },
            e.createElement("strong", null, c.name),
            c.description ? e.createElement(
              "div",
              { style: { color: "#666", fontSize: 12 } },
              c.description
            ) : null
          )
        )
      ) : null,
      r.capabilities ? e.createElement(
        "div",
        { style: { marginTop: 16 } },
        e.createElement("h4", null, "能力"),
        e.createElement(
          q,
          null,
          e.createElement(
            B,
            {
              color: r.capabilities.streaming ? "green" : "default"
            },
            "Streaming"
          ),
          e.createElement(
            B,
            {
              color: r.capabilities.push_notifications ? "green" : "default"
            },
            "Push Notifications"
          )
        )
      ) : null,
      r.error ? e.createElement(
        "div",
        {
          style: {
            marginTop: 16,
            padding: "8px 12px",
            background: "#fff2f0",
            border: "1px solid #ffccc7",
            borderRadius: 6,
            fontSize: 12,
            color: "#ff4d4f"
          }
        },
        r.error
      ) : null,
      e.createElement(ut, null),
      e.createElement(
        q,
        null,
        e.createElement(
          P,
          {
            type: "primary",
            icon: be ? e.createElement(be) : null,
            loading: p,
            onClick: ge
          },
          "刷新 Agent Card"
        ),
        e.createElement(
          P,
          {
            danger: !0,
            icon: Je ? e.createElement(Je) : null,
            onClick: L
          },
          "删除"
        )
      )
    ) : null, se = e.createElement(
      it,
      {
        title: A ? "注册远程 A2A Agent" : (r == null ? void 0 : r.name) || (r == null ? void 0 : r.alias) || "Agent 详情",
        open: u,
        onClose: d,
        width: 480,
        footer: A ? e.createElement(
          q,
          { style: { float: "right" } },
          e.createElement(P, { onClick: d }, "取消"),
          e.createElement(
            P,
            { type: "primary", loading: z, onClick: m },
            "注册"
          )
        ) : null
      },
      A ? ye : ie
    ), ae = e.createElement(
      "div",
      { style: { marginBottom: 16 } },
      e.createElement(
        "div",
        {
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }
        },
        e.createElement("h2", { style: { margin: 0 } }, "A2A 远程 Agent"),
        e.createElement(
          q,
          null,
          e.createElement(
            P,
            {
              icon: be ? e.createElement(be) : null,
              onClick: S,
              loading: a
            },
            "刷新列表"
          ),
          e.createElement(
            P,
            {
              type: "primary",
              icon: He ? e.createElement(He) : null,
              onClick: N
            },
            "注册 Agent"
          )
        )
      ),
      e.createElement(
        "div",
        {
          style: {
            marginTop: 8,
            fontSize: 12,
            color: "#8c8c8c",
            lineHeight: 1.6
          }
        },
        Se ? e.createElement(Se, {
          style: { marginRight: 4, color: "#faad14" }
        }) : null,
        "当前 A2A 功能仅支持 CloudPaw 插件连接阿里云 Skills 门户 Agent，连接其他 Agent 可能存在不兼容问题。"
      )
    ), X = a ? e.createElement(
      "div",
      { style: { textAlign: "center", padding: 60 } },
      e.createElement(Te, { size: "large" })
    ) : n.length === 0 ? e.createElement(dt, { description: "暂无注册的远程 A2A Agent" }) : e.createElement(
      "div",
      {
        style: {
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 12
        }
      },
      ...n.map(
        (c) => e.createElement(ft, {
          key: c.alias || c.url,
          agent: c,
          onClick: () => i(c)
        })
      )
    );
    return e.createElement(
      "div",
      { style: { padding: 24 } },
      ae,
      X,
      se
    );
  }
  const gt = "__A2A_STREAM_START__", yt = "A2A_STREAM_START", pe = /* @__PURE__ */ new Set();
  function Ie(t) {
    return t ? t.includes(gt) || t.includes(yt) : !1;
  }
  function Re(t) {
    var n, o;
    return t.getAttribute("data-msg-id") || t.getAttribute("data-message-id") || ((n = t.closest("[data-msg-id]")) == null ? void 0 : n.getAttribute("data-msg-id")) || ((o = t.closest("[data-message-id]")) == null ? void 0 : o.getAttribute("data-message-id")) || null;
  }
  function ht(t) {
    if (Ie(t.innerHTML) || Ie(t.textContent))
      return t;
    const n = document.createTreeWalker(
      t,
      NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT
    );
    for (; n.nextNode(); ) {
      const o = n.currentNode, a = o.nodeType === Node.TEXT_NODE ? o.textContent : o.innerHTML;
      if (Ie(a)) {
        const l = o.nodeType === Node.TEXT_NODE ? o.parentElement : o;
        if (l) return l;
      }
    }
    return null;
  }
  async function Pe(t) {
    var g, A;
    const n = window.QwenPaw;
    if (!(n != null && n.host)) {
      console.warn("[a2a] QwenPaw.host not available");
      return;
    }
    const { getApiUrl: o, getApiToken: a } = n.host, l = o("/a2a/call/stream"), u = a();
    console.log("[a2a] Subscribing to SSE stream:", l);
    const s = document.createElement("div");
    s.style.cssText = "background:#f6ffed;border:1px solid #b7eb8f;border-radius:8px;padding:12px 16px;margin:4px 0;font-size:13px;white-space:pre-wrap;word-break:break-word;color:#262626;min-height:24px;", s.textContent = "正在连接远程 Agent...", t.textContent = "", t.appendChild(s);
    const r = new AbortController();
    try {
      const h = {
        Accept: "text/event-stream"
      };
      u && (h.Authorization = `Bearer ${u}`);
      try {
        const E = sessionStorage.getItem("qwenpaw-agent-storage") || localStorage.getItem("qwenpaw-agent-storage"), S = (A = (g = JSON.parse(E || "{}")) == null ? void 0 : g.state) == null ? void 0 : A.selectedAgent;
        S && (h["X-Agent-Id"] = S);
      } catch {
      }
      console.log("[a2a] Fetching SSE with headers:", h);
      const z = await fetch(l, { headers: h, signal: r.signal });
      if (console.log("[a2a] SSE response status:", z.status), !z.ok) {
        const E = await z.text().catch(() => "");
        s.textContent = `SSE 连接失败 (${z.status}): ${E.slice(0, 100)}`, s.style.borderColor = "#ff4d4f", s.style.background = "#fff1f0";
        return;
      }
      if (!z.body) {
        s.textContent = "SSE 连接失败：无响应体", s.style.borderColor = "#ff4d4f", s.style.background = "#fff1f0";
        return;
      }
      const D = z.body.getReader(), p = new TextDecoder();
      let C = "";
      for (; ; ) {
        const { done: E, value: S } = await D.read();
        if (E) {
          console.log("[a2a] SSE stream ended (done)");
          break;
        }
        C += p.decode(S, { stream: !0 });
        const N = C.split(`
`);
        C = N.pop() || "";
        for (const i of N)
          if (i.startsWith("data: "))
            try {
              const d = JSON.parse(i.slice(6));
              if (console.log("[a2a] SSE event:", d), d.done) {
                d.error && (s.textContent = `错误: ${d.error}`, s.style.borderColor = "#ff4d4f", s.style.background = "#fff1f0"), console.log("[a2a] SSE done signal received");
                return;
              }
              typeof d.response_text == "string" && d.response_text && (s.textContent = d.response_text);
            } catch (d) {
              console.warn("[a2a] SSE parse error:", d, "line:", i);
            }
      }
    } catch (h) {
      (h == null ? void 0 : h.name) !== "AbortError" && (console.error("[a2a] SSE subscription error:", h), s.textContent = `连接出错: ${(h == null ? void 0 : h.message) || h}`, s.style.borderColor = "#ff4d4f", s.style.background = "#fff1f0");
    }
  }
  function Et() {
    console.log("[a2a] Initializing stream interceptor");
    function t(l) {
      if (l.nodeType !== Node.ELEMENT_NODE) return;
      const u = l, s = Re(u);
      if (s && pe.has(s)) return;
      const r = ht(u);
      r && (console.log("[a2a] Marker detected in DOM, msgId:", s), s && pe.add(s), Pe(r));
    }
    new MutationObserver((l) => {
      for (const u of l) {
        for (const s of u.addedNodes)
          t(s);
        u.target.nodeType === Node.ELEMENT_NODE && t(u.target);
      }
    }).observe(document.body, {
      childList: !0,
      subtree: !0,
      characterData: !0,
      characterDataOldValue: !0
    });
    const o = setInterval(() => {
      const l = document.evaluate(
        "//text()[contains(., 'A2A_STREAM_START')]",
        document.body,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
      );
      for (let u = 0; u < l.snapshotLength; u++) {
        const r = l.snapshotItem(u).parentElement;
        if (r) {
          const g = Re(r);
          if (g && pe.has(g)) continue;
          console.log("[a2a] Marker found in periodic scan, msgId:", g), g && pe.add(g), Pe(r);
        }
      }
    }, 500);
    window.addEventListener("beforeunload", () => clearInterval(o));
    const a = document.evaluate(
      "//text()[contains(., 'A2A_STREAM_START')]",
      document.body,
      null,
      XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
      null
    );
    for (let l = 0; l < a.snapshotLength; l++) {
      const s = a.snapshotItem(l).parentElement;
      if (s) {
        const r = Re(s);
        r && pe.add(r), console.log("[a2a] Marker found in existing DOM, msgId:", r), Pe(s);
      }
    }
  }
  (Ke = (Fe = window.QwenPaw).registerToolRender) == null || Ke.call(Fe, "cloudpaw", {
    proposal_choice: st,
    manage_prd: at,
    a2a_call: lt
  }), (Xe = (qe = window.QwenPaw).registerRoutes) == null || Xe.call(qe, "cloudpaw", [
    {
      path: "/a2a",
      component: pt,
      label: "A2A",
      icon: "🔗",
      priority: 10
    }
  ]), At(), bt(), Et();
}
function At() {
  const e = "qwenpaw-last-used-agent", M = "qwenpaw-agent-storage", J = "cloudpaw-first-install", K = "cloud-orchestrator";
  if (localStorage.getItem(J)) return;
  localStorage.setItem(J, "true");
  function Q() {
    localStorage.setItem(e, K);
    try {
      const W = localStorage.getItem(M);
      if (W) {
        const $ = JSON.parse(W);
        $.state = $.state || {}, $.state.selectedAgent = K, localStorage.setItem(M, JSON.stringify($));
      } else
        localStorage.setItem(
          M,
          JSON.stringify({
            version: 0,
            state: {
              selectedAgent: K,
              agents: [],
              lastChatIdByAgent: {}
            }
          })
        );
    } catch {
    }
    try {
      const W = sessionStorage.getItem(M);
      if (W) {
        const $ = JSON.parse(W);
        $.state = $.state || {}, $.state.selectedAgent = K, sessionStorage.setItem(M, JSON.stringify($));
      } else
        sessionStorage.setItem(
          M,
          JSON.stringify({
            version: 0,
            state: {
              selectedAgent: K,
              agents: [],
              lastChatIdByAgent: {}
            }
          })
        );
    } catch {
    }
  }
  Q(), window.addEventListener(
    "beforeunload",
    () => {
      Q();
    },
    { once: !0 }
  ), console.info(
    "[cloudpaw] Set default agent to cloud-orchestrator for first-time user"
  ), window.location.reload();
}
function bt() {
  var q;
  const e = (q = window.QwenPaw) == null ? void 0 : q.modules;
  if (!e) return;
  const M = e["Chat/OptionsPanel/defaultConfig"];
  if (!(M != null && M.configProvider)) {
    console.warn(
      "[cloudpaw] configProvider not found — skipping welcome/theme patch"
    );
    return;
  }
  const J = M.configProvider, K = J.getConfig.bind(J), Q = "https://gw.alicdn.com/imgextra/i2/O1CN01pyXzjQ1EL1PuZMlSd_!!6000000000334-2-tps-288-288.png", W = {
    zh: "CloudPaw 插件提示",
    en: "CloudPaw Plugin Tips",
    ja: "CloudPaw プラグインのヒント",
    ru: "Подсказки плагина CloudPaw"
  }, $ = {
    zh: `告诉 CloudPaw 你想做什么，它会自动帮你完成云资源管理、基础设施编排与应用创建上云等任务。
⚠️ 使用前请在左上角下拉框切换到「CloudPaw-Master」，否则功能无法正常使用！
对于复杂的长程任务，建议使用 /mission 命令启动 Mission Mode 来自动拆解和执行。`,
    en: `Tell CloudPaw what you want to do — it will automatically handle cloud resource management, infrastructure orchestration, and application deployment.
⚠️ Please switch to 'CloudPaw-Master' from the dropdown in the top-left corner before use — features won't work otherwise!
For complex, multi-step tasks, use /mission to start Mission Mode for automated decomposition and execution.`,
    ja: `CloudPaw にやりたいことを伝えるだけで、クラウドリソース管理、インフラ構成、アプリケーションのデプロイなどを自動で行います。
⚠️ 使用前に左上のドロップダウンから「CloudPaw-Master」に切り替えてください。切り替えないと機能が正常に動作しません！
複雑なタスクには /mission コマンドで Mission Mode を起動し、自動分解・実行できます。`,
    ru: `Расскажите CloudPaw, что вы хотите сделать — он автоматически выполнит управление облачными ресурсами, оркестрацию инфраструктуры и развёртывание приложений.
⚠️ Перед началом переключитесь на 'CloudPaw-Master' в выпадающем списке в левом верхнем углу — иначе функции не будут работать!
Для сложных задач используйте /mission для автоматической декомпозиции и выполнения.`
  }, B = {
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
  function fe() {
    const P = localStorage.getItem("language") || "";
    return P ? P.split("-")[0] : (navigator.language || "").split("-")[0] || "en";
  }
  if (J.getGreeting = () => W[fe()] || W.en, J.getDescription = () => $[fe()] || $.en, J.getPrompts = () => B[fe()] || B.en, J.getConfig = function(P) {
    var me;
    const Y = K(P);
    return {
      ...Y,
      theme: {
        ...Y.theme,
        leftHeader: {
          ...(me = Y.theme) == null ? void 0 : me.leftHeader,
          title: "Work with CloudPaw"
        }
      },
      welcome: {
        ...Y.welcome,
        avatar: Q
      }
    };
  }, !document.getElementById("cloudpaw-welcome-style")) {
    const P = document.createElement("style");
    P.id = "cloudpaw-welcome-style", P.textContent = `
      [class*="chat-anywhere-welcome-default"] [class*="description"],
      [class*="message-list-welcome"] [class*="description"] {
        white-space: pre-line !important;
        text-align: center !important;
      }
    `, document.head.appendChild(P);
  }
  console.info("[cloudpaw] Patched welcome config & theme via configProvider");
}
xt();
