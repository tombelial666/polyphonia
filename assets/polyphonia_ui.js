/**
 * Polyphonia: assist panel, layout grid, string visibility, fingering hints,
 * MusicXML snapshot export, fullscreen bridge (pywebview + Fullscreen API).
 * Depends on globals from build_index inline script (jQuery, getScaleByCode, …).
 */
(function () {
  "use strict";

  var STORAGE_LAYOUT = "polyphonia_layout_class";
  var STORAGE_FRET_BOX = "polyphonia_fret_box_layout";
  var STORAGE_ASSIST = "polyphonia_assist_draft";
  var STORAGE_DIALOG_MD = "polyphonia_dialog_md_enabled";
  var STORAGE_ASSIST_SEND_MODE = "polyphonia_assist_send_mode";
  var lastStringCount = null;

  function getPolyMode() {
    try {
      var u = new URL(window.location.href);
      var m = (u.searchParams.get("poly_mode") || "").toLowerCase();
      if (m === "offline" || m === "assist") return m;
      var h = (u.hash || "").replace(/^#/, "");
      if (h.indexOf("poly_mode=") === 0) {
        var mv = h.slice("poly_mode=".length).split(/[&?]/)[0].toLowerCase();
        if (mv === "offline" || mv === "assist") return mv;
      }
    } catch (e0) {}
    return "offline";
  }

  function isAssistMode() {
    return getPolyMode() === "assist";
  }

  function applyPolyModeClass() {
    var m = getPolyMode();
    try {
      $("html").removeClass("poly_mode_offline poly_mode_assist").addClass("poly_mode_" + m);
      window.__POLYPHONIA_UI_MODE__ = m;
    } catch (e1) {}
  }

  function getPolyView() {
    try {
      var u = new URL(window.location.href);
      return (u.searchParams.get("poly_view") || "").toLowerCase();
    } catch (e0) {}
    return "";
  }

  function applyPolyViewClass() {
    var v = getPolyView();
    try {
      $("html").removeClass("poly_view_assist");
      if (v === "assist") $("html").addClass("poly_view_assist");
    } catch (e1) {}
  }

  function syncSettingsModeRadios() {
    var m = getPolyMode();
    $('input[name="settings_poly_mode_pick"][value="' + m + '"]').prop("checked", true);
  }

  function applyPolyModeRuntime(newMode) {
    if (newMode !== "offline" && newMode !== "assist") return;
    var bridge = $("#settings_poly_mode_bridge");
    var hadApi = !!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_poly_mode === "function");
    var step = hadApi ? callPyApi("set_poly_mode", JSON.stringify({ mode: newMode })) : Promise.resolve();
    step
      .then(function () {
        try {
          var u = new URL(window.location.href);
          // Prefer hash for file:// navigation stability on WebView2; keep query if present.
          u.hash = "poly_mode=" + newMode;
          if (u.searchParams && u.searchParams.has("poly_mode")) u.searchParams.set("poly_mode", newMode);
          window.history.replaceState({}, "", u.toString());
        } catch (e2) {}
        applyPolyModeClass();
        if (newMode === "offline") {
          $("#assist_panel").addClass("hidden").attr("aria-hidden", "true");
        }
        $("#settings_poly_mode").text(getPolyMode());
        syncSettingsModeRadios();
        refreshSettingsMdBridge();
        syncAssistOpenaiControls();
        if (bridge.length) {
          if (hadApi) {
            bridge.text(
              "Режим действует до закрытия окна. Новый запуск phrygian_app.py снова спросит / возьмёт POLYPHONIA_MODE."
            );
          } else {
            bridge.text(
              "Режим в странице изменён (без pywebview). Для GPT/Assist из Python запустите phrygian_app.py и при необходимости выставьте режим здесь снова."
            );
          }
        }
      })
      .catch(function () {
        if (bridge.length) bridge.text("Не удалось выставить режим в Python (нужен pywebview с актуальным phrygian_app.py).");
      });
  }

  function pcToPitchSharp(pc) {
    var map = [
      { step: "C", alter: 0 },
      { step: "C", alter: 1 },
      { step: "D", alter: 0 },
      { step: "D", alter: 1 },
      { step: "E", alter: 0 },
      { step: "F", alter: 0 },
      { step: "F", alter: 1 },
      { step: "G", alter: 0 },
      { step: "G", alter: 1 },
      { step: "A", alter: 0 },
      { step: "A", alter: 1 },
      { step: "B", alter: 0 }
    ];
    return map[((pc % 12) + 12) % 12];
  }

  function getInstrumentContext() {
    return {
      instrument: $("#app_instrument_select").val(),
      note: $("#note").val(),
      scale: $("#scale").val(),
      accidental: $("#accidental").val(),
      capo: $("#capo_fret").val(),
      lefty: $("#lefty").prop("checked"),
      tuning: $("#tuning").val(),
      fretBoxLayout: ($("#poly_fret_box_select").val() || "fret_box_off"),
      uiMode: getPolyMode(),
      openaiBridge: openaiBridgeAvailable(),
      riffDraft: window.__poly_riff_draft || null
    };
  }

  function pywebviewOpenaiCallable() {
    return !!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.openai_chat === "function");
  }

  function pywebviewDialogMdCallable() {
    return !!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.append_assist_dialog_md === "function");
  }

  function openaiBridgeAvailable() {
    return isAssistMode() && pywebviewOpenaiCallable();
  }

  function formatOpenAiConnectionLine(o) {
    if (!o || !o.ok) return "Не удалось получить сводку подключения.";
    if (o.ui_mode === "offline") return "Режим офлайн — GPT из окна приложения отключён.";
    if (o.source === "env") return "Ключ: из переменной окружения OPENAI_API_KEY (приоритет над сессионным ключом).";
    if (o.source === "session") return "Ключ: сессионный в RAM (поле Assist или Настройки).";
    return "Ключ не задан: задайте OPENAI_API_KEY при запуске или сохраните сессионный ключ.";
  }

  function formatOpenAiModelLine(o) {
    if (!o || !o.ok || o.ui_mode === "offline") return "";
    return "Модель по умолчанию: " + (o.model_default || "gpt-4o-mini");
  }

  function refreshOpenaiConnectionFromHost() {
    if (!isAssistMode()) {
      $("#assist_openai_summary").text("");
      $("#settings_gpt_line").text("В режиме assist доступен GPT из этого окна (через phrygian_app.py). Сейчас включён офлайн.");
      $("#settings_gpt_model").text("");
      return;
    }
    if (!pywebviewOpenaiCallable() || typeof window.pywebview.api.get_openai_connection !== "function") {
      $("#assist_openai_summary").text("");
      $("#settings_gpt_line").text(
        "Нет моста pywebview — ввод ключа в UI недоступен. Задайте OPENAI_API_KEY в окружении до запуска phrygian_app.py."
      );
      $("#settings_gpt_model").text("");
      return;
    }
    callPyApi("get_openai_connection", "")
      .then(function (raw) {
        var o = typeof raw === "string" ? JSON.parse(raw) : raw;
        var line = formatOpenAiConnectionLine(o);
        var model = formatOpenAiModelLine(o);
        $("#assist_openai_summary").text(line);
        $("#settings_gpt_line").text(line);
        $("#settings_gpt_model").text(model);
      })
      .catch(function () {
        $("#assist_openai_summary").text("");
        $("#settings_gpt_line").text("Не удалось прочитать сводку (Python API).");
        $("#settings_gpt_model").text("");
      });
  }

  function callPyApi(methodName, arg) {
    var api = window.pywebview && window.pywebview.api;
    if (!api || typeof api[methodName] !== "function") {
      return Promise.reject(new Error("no_py_api"));
    }
    try {
      var r = api[methodName](arg);
      if (r && typeof r.then === "function") return r;
      return Promise.resolve(r);
    } catch (e) {
      return Promise.reject(e);
    }
  }

  function logToHost(eventName, payload) {
    try {
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.log_client_event === "function") {
        var p = payload || {};
        p.event = eventName;
        p.href = String(window.location && window.location.href ? window.location.href : "");
        callPyApi("log_client_event", JSON.stringify(p)).catch(function () {});
      }
    } catch (e0) {}
  }

  // Global error hooks for easier debugging
  window.addEventListener("error", function (e) {
    try {
      var msg = e && e.message ? e.message : String(e);
      console.error("[Polyphonia] window.error:", msg, e && e.filename ? e.filename : "", e && e.lineno ? e.lineno : "");
      logToHost("window_error", { message: msg, filename: e && e.filename, lineno: e && e.lineno, colno: e && e.colno });
    } catch (e0) {}
  });
  window.addEventListener("unhandledrejection", function (e) {
    try {
      var r = e && e.reason ? e.reason : e;
      var msg = r && r.message ? r.message : String(r);
      console.error("[Polyphonia] unhandledrejection:", msg, r);
      logToHost("unhandledrejection", { message: msg });
    } catch (e0) {}
  });

  function syncAssistOpenaiControls() {
    if (!isAssistMode()) {
      $("#assist_openai_save, #assist_openai_clear, #assist_ask_gpt, #assist_openai_key").prop("disabled", true);
      $("#assist_openai_status").text("");
      $("#assist_openai_summary").text("");
      $("#settings_openai_key, #settings_openai_save, #settings_openai_clear, #settings_gpt_ping").prop("disabled", true);
      $("#settings_claude_key, #settings_claude_save, #settings_claude_clear, #settings_claude_validate").prop(
        "disabled",
        true
      );
      $("#settings_gpt_line").text("GPT в UI доступен в режиме assist.");
      $("#settings_gpt_model").text("");
      return;
    }
    var on = pywebviewOpenaiCallable();
    $("#assist_openai_save, #assist_openai_clear, #assist_ask_gpt, #assist_openai_key").prop("disabled", !on);
    $("#settings_openai_key, #settings_openai_save, #settings_openai_clear, #settings_gpt_ping").prop("disabled", !on);
    $("#settings_claude_key, #settings_claude_save, #settings_claude_clear, #settings_claude_validate").prop(
      "disabled",
      !on
    );
    $("#assist_openai_status").text(
      on ? "" : "Сейчас не pywebview — вызов GPT из приложения недоступен (откройте через phrygian_app.py)."
    );
    refreshOpenaiConnectionFromHost();
  }

  function getScaleNoteKeysForExport() {
    if (typeof getScaleByCode !== "function" || typeof getCurrentRootKey !== "function") return [];
    if (typeof getCurrentScaleNoteKeys !== "function") return [];
    var scaleInfo = getScaleByCode($("#scale").val());
    var rootKey = getCurrentRootKey();
    if (!scaleInfo || rootKey < 0) return [];
    return getCurrentScaleNoteKeys(rootKey, scaleInfo);
  }

  function buildMusicXmlFromScale(keys) {
    var title = "Polyphonia scale snapshot";
    try {
      title = ($("#info_scale_name").text() || title).replace(/</g, "");
    } catch (e) {}
    var notesXml = "";
    for (var i = 0; i < keys.length; i++) {
      var p = pcToPitchSharp(keys[i]);
      var alterXml = p.alter !== 0 ? "<alter>" + p.alter + "</alter>" : "";
      notesXml +=
        "<note><pitch><step>" +
        p.step +
        "</step>" +
        alterXml +
        "<octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>\n";
    }
    return (
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<!DOCTYPE score-partwise PUBLIC "-//Recordings//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n' +
      '<score-partwise version="3.1">\n' +
      "<work><work-title>" +
      escapeXml(title) +
      "</work-title></work>\n" +
      '<part-list><score-part id="P1"><part-name>Polyphonia</part-name></score-part></part-list>\n' +
      '<part id="P1">\n' +
      "<measure number=\"1\">\n" +
      "<attributes>\n" +
      "<divisions>1</divisions>\n" +
      "<key><fifths>0</fifths></key>\n" +
      "<time><beats>4</beats><beat-type>4</beat-type></time>\n" +
      "<clef><sign>G</sign><line>2</line></clef>\n" +
      "</attributes>\n" +
      notesXml +
      "</measure>\n" +
      "</part>\n" +
      "</score-partwise>\n"
    );
  }

  function escapeXml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function downloadText(filename, text, mime) {
    var blob = new Blob([text], { type: mime || "application/octet-stream" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 2500);
  }

  function exportMusicXMLScaleSnapshot() {
    var keys = getScaleNoteKeysForExport();
    if (!keys.length) {
      appendAssistLine("system", "Cannot build MusicXML: no scale/root context.");
      return;
    }
    var xml = buildMusicXmlFromScale(keys);
    var safe = ($("#note").val() || "x") + "-" + ($("#scale").val() || "scale");
    downloadText("polyphonia-" + safe + "-snapshot.musicxml", xml, "application/vnd.recordare.musicxml+xml");
  }

  function suggestFinger(stringIndex, fret) {
    var f = Math.max(0, parseInt(fret, 10) || 0);
    var base = 1 + (stringIndex % 3);
    var off = f % 4;
    return ((base + off - 1) % 4) + 1;
  }

  function applyFingeringHints() {
    $("#fret_note_con .finger_hint").remove();
    if (!$("#poly_fingering_toggle").is(":checked")) return;
    var capo = parseInt($("#capo_fret").val() || "0", 10);
    $("#fret_note_con .sf.in_scale").each(function () {
      var $cell = $(this);
      var cid = $cell.attr("id") || "";
      if (cid.indexOf("s_x_") === 0) return;
      var m = ($cell.attr("class") || "").match(/\bs_(\d+)\b/);
      if (!m) return;
      var s = parseInt(m[1], 10);
      var $fret = $cell.closest("[id^='f_']");
      var fid = $fret.attr("id") || "";
      var fretNum = parseInt(fid.replace(/^f_/, ""), 10);
      if (isNaN(fretNum) || fretNum < capo) return;
      var finger = suggestFinger(s, fretNum);
      $cell.append('<span class="finger_hint" title="Heuristic fingering (Assumption)">' + finger + "</span>");
    });
  }

  function readStringVisibilityState() {
    var st = {};
    $("#string_visibility_ops input.poly_str_vis").each(function () {
      var s = parseInt($(this).attr("data-s"), 10);
      st[s] = $(this).is(":checked");
    });
    return st;
  }

  function applyStringHideClasses() {
    var $disp = $("#stringed_display");
    if (!$disp.length) return;
    var s;
    for (s = 0; s < 16; s++) {
      $disp.removeClass("poly_hide_s" + s);
    }
    $("#string_visibility_ops input.poly_str_vis").each(function () {
      var si = parseInt($(this).attr("data-s"), 10);
      if (!$(this).is(":checked")) $disp.addClass("poly_hide_s" + si);
    });
  }

  function fretBox32GroupIndex(f, capo) {
    var p = f - capo;
    if (p < 0) return -1;
    return Math.floor(p / 5) * 2 + (p % 5 < 3 ? 0 : 1);
  }

  function fretBox32IsStart(f, capo) {
    var p = f - capo;
    if (p < 0) return false;
    return p % 5 === 0 || p % 5 === 3;
  }

  function applyFretBoxLayout() {
    var $disp = $("#stringed_display");
    var piano = $("#app_instrument_select").val() === "piano";
    if ($("#poly_fret_box_select").length) {
      $("#poly_fret_box_select").prop("disabled", !!piano);
    }
    $("#fret_note_con > [id^='f_']").removeClass("poly_fb_start poly_fb_alt0 poly_fb_alt1");
    $("#frets_con > [id^='fret_']").removeClass("poly_fb_start poly_fb_alt0 poly_fb_alt1");
    if (!$disp.length || piano) {
      $disp.removeClass("poly_fret_boxes poly_fb_mode_3 poly_fb_mode_32");
      return;
    }
    var mode = ($("#poly_fret_box_select").val() || "fret_box_off");
    $disp.removeClass("poly_fret_boxes poly_fb_mode_3 poly_fb_mode_32");
    if (mode === "fret_box_off") return;
    $disp.addClass("poly_fret_boxes");
    if (mode === "fret_box_3") $disp.addClass("poly_fb_mode_3");
    else if (mode === "fret_box_32") $disp.addClass("poly_fb_mode_32");
    var capo = parseInt($("#capo_fret").val() || "0", 10) || 0;

    function markCol(fid, fretNum) {
      var $nc = $("#" + fid);
      var $fc = $("#fret_" + fretNum);
      if (!$nc.length) return;
      var g;
      var isStart = false;
      if (mode === "fret_box_3") {
        g = Math.floor((fretNum - capo) / 3);
        isStart = fretNum >= capo && (fretNum - capo) % 3 === 0;
      } else {
        g = fretBox32GroupIndex(fretNum, capo);
        isStart = fretBox32IsStart(fretNum, capo);
      }
      if (g < 0) return;
      var alt = g % 2 === 1 ? "poly_fb_alt1" : "poly_fb_alt0";
      $nc.addClass(alt);
      if ($fc.length) $fc.addClass(alt);
      if (isStart) {
        $nc.addClass("poly_fb_start");
        if ($fc.length) $fc.addClass("poly_fb_start");
      }
    }

    $("#fret_note_con > [id^='f_']").each(function () {
      var id = $(this).attr("id") || "";
      var m = id.match(/^f_(\d+)$/);
      if (!m) return;
      markCol(id, parseInt(m[1], 10));
    });
  }

  function rebuildStringVisibilityUi() {
    var host = $("#string_visibility_ops");
    if (!host.length) return;
    var prev = readStringVisibilityState();
    var n = window.instrumentInfo && window.instrumentInfo.notes ? window.instrumentInfo.notes.length : 0;
    if (!n) {
      host.empty();
      lastStringCount = 0;
      return;
    }
    var html = "";
    for (var s = 0; s < n; s++) {
      var checked = prev[s] !== false;
      html +=
        '<label class="poly_str_lab"><input type="checkbox" class="poly_str_vis" data-s="' +
        s +
        '"' +
        (checked ? " checked" : "") +
        "> S" +
        (s + 1) +
        "</label>";
    }
    host.html(html);
    lastStringCount = n;
    applyStringHideClasses();
  }

  function afterRenderScalePage() {
    var n = window.instrumentInfo && window.instrumentInfo.notes ? window.instrumentInfo.notes.length : 0;
    if (n !== lastStringCount) rebuildStringVisibilityUi();
    applyStringHideClasses();
    applyFretBoxLayout();
    applyFingeringHints();
  }

  function wrapRenderScalePage() {
    var orig = window.renderScalePage;
    if (typeof orig !== "function" || orig.__polyWrapped) return;
    function wrapped() {
      var ret = orig.apply(this, arguments);
      afterRenderScalePage();
      return ret;
    }
    wrapped.__polyWrapped = true;
    window.renderScalePage = wrapped;
  }

  function toggleFullscreen() {
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.fullscreen_toggle === "function") {
      window.pywebview.api.fullscreen_toggle();
      return;
    }
    var de = document.documentElement;
    if (!document.fullscreenElement) {
      var p = de.requestFullscreen && de.requestFullscreen();
      if (p && p.catch) p.catch(function () {});
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }

  function isDialogMdEnabled() {
    if (!isAssistMode()) return false;
    try {
      var v = localStorage.getItem(STORAGE_DIALOG_MD);
      if (v === "0") return false;
      if (v === "1") return true;
      return true;
    } catch (e0) {
      return true;
    }
  }

  function setDialogMdEnabled(on) {
    try {
      localStorage.setItem(STORAGE_DIALOG_MD, on ? "1" : "0");
    } catch (e1) {}
  }

  function persistAssistDialogMd(role, text) {
    if (!isAssistMode() || !isDialogMdEnabled()) return;
    if (!pywebviewDialogMdCallable()) return;
    callPyApi("append_assist_dialog_md", JSON.stringify({ role: role, text: text })).catch(function () {});
  }

  function appendAssistLine(role, text) {
    var esc = $("<div/>").text(text).html();
    var cls =
      role === "user"
        ? "assist_msg_user"
        : role === "gpt"
          ? "assist_msg_gpt"
          : role === "gpt_error"
            ? "assist_msg_gpt_error"
            : "assist_msg_sys";
    $("#assist_messages").append('<div class="assist_msg ' + cls + '">' + esc + "</div>");
    $("#assist_messages").scrollTop($("#assist_messages")[0].scrollHeight);
    persistAssistDialogMd(role, text);
  }

  function formatGptErrorMessage(raw) {
    var s = String(raw || "").trim();
    if (!s) return "Ошибка GPT.";
    try {
      var o = JSON.parse(s);
      if (o && o.error && (o.error.message || o.error.type || o.error.code)) {
        var msg = String(o.error.message || "Ошибка").trim();
        var code = String(o.error.code || o.error.type || "").trim();
        return code ? msg + " (" + code + ")" : msg;
      }
    } catch (e0) {}
    // keep it short: raw API payloads are noisy
    if (s.length > 420) return s.slice(0, 420) + "…";
    return s;
  }

  function newTraceId() {
    try {
      if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    } catch (e0) {}
    try {
      return (
        "t-" +
        Date.now().toString(36) +
        "-" +
        Math.floor(Math.random() * 1e9).toString(36)
      );
    } catch (e1) {}
    return "t-" + String(Date.now());
  }

  function openAssist() {
    if (!isAssistMode()) return;
    $("#assist_panel").removeClass("hidden").attr("aria-hidden", "false");
    syncAssistOpenaiControls();
  }

  function closeAssist() {
    $("#assist_panel").addClass("hidden").attr("aria-hidden", "true");
  }

  function saveAssistDraft() {
    try {
      localStorage.setItem(STORAGE_ASSIST, $("#assist_input").val() || "");
    } catch (e) {}
  }

  function loadAssistDraft() {
    try {
      var t = localStorage.getItem(STORAGE_ASSIST);
      if (t) $("#assist_input").val(t);
    } catch (e) {}
  }

  function applyLayoutClass(cls) {
    var $g = $("#poly_grid");
    if (!$g.length) return;
    $g.removeClass("poly_layout_stack poly_layout_wide");
    $g.addClass(cls);
    try {
      localStorage.setItem(STORAGE_LAYOUT, cls);
    } catch (e) {}
  }

  function initLayoutFromStorage() {
    var v = "poly_layout_stack";
    try {
      v = localStorage.getItem(STORAGE_LAYOUT) || v;
    } catch (e) {}
    if (v !== "poly_layout_wide" && v !== "poly_layout_stack") v = "poly_layout_stack";
    $("#poly_layout_select").val(v);
    applyLayoutClass(v);
  }

  function initFretBoxFromStorage() {
    var fb = "fret_box_off";
    try {
      fb = localStorage.getItem(STORAGE_FRET_BOX) || fb;
    } catch (e) {}
    if (fb !== "fret_box_off" && fb !== "fret_box_3" && fb !== "fret_box_32") fb = "fret_box_off";
    if ($("#poly_fret_box_select").length) $("#poly_fret_box_select").val(fb);
  }

  function persistFretBoxMode(val) {
    try {
      localStorage.setItem(STORAGE_FRET_BOX, val);
    } catch (e) {}
  }

  function exportSession(text) {
    try {
      localStorage.setItem("polyphonia_session_dump", text || "");
    } catch (e) {}
  }

  function initAssistHandlers() {
    $("#poly_assist_btn").on("click", function () {
      openAssist();
    });
    $("#assist_close").on("click", function () {
      closeAssist();
    });
    function setSendMode(mode) {
      if (mode !== "draft" && mode !== "gpt") mode = "draft";
      try {
        localStorage.setItem(STORAGE_ASSIST_SEND_MODE, mode);
      } catch (e0) {}
      $("#assist_mode_draft").toggleClass("selected", mode === "draft");
      $("#assist_mode_gpt").toggleClass("selected", mode === "gpt");
      $("#assist_send").text(mode === "gpt" ? "Отправить в GPT" : "Сохранить черновик");
    }

    function getSendMode() {
      var v = "draft";
      try {
        v = localStorage.getItem(STORAGE_ASSIST_SEND_MODE) || v;
      } catch (e0) {}
      return v === "gpt" ? "gpt" : "draft";
    }

    $("#assist_settings").on("click", function () {
      openSettings();
    });
    $("#assist_mode_draft").on("click", function () {
      setSendMode("draft");
    });
    $("#assist_mode_gpt").on("click", function () {
      setSendMode("gpt");
    });

    function doDraftSend(t) {
      var t = ($("#assist_input").val() || "").trim();
      if (!t) return;
      appendAssistLine("user", t);
      window.__poly_riff_draft = { text: t, context: getInstrumentContext() };
      appendAssistLine(
        "system",
        "Offline draft (Assumption). Context JSON:\n" + JSON.stringify(getInstrumentContext(), null, 2)
      );
      appendAssistLine(
        "system",
        "Use «Apply to fretboard» only after review. It re-syncs highlights from the current form state (deterministic)."
      );
      var $row = $('<div class="assist_msg assist_msg_sys"></div>');
      var $btn = $('<button type="button" class="assist_inline_btn">Apply to fretboard…</button>');
      $row.append($btn);
      $("#assist_messages").append($row);
      $btn.on("click", function () {
        $("#assist_pending").removeClass("hidden");
      });
      $("#assist_input").val("");
      saveAssistDraft();
    }
    $("#assist_apply_cancel").on("click", function () {
      $("#assist_pending").addClass("hidden");
    });
    $("#assist_apply_confirm").on("click", function () {
      $("#assist_pending").addClass("hidden");
      if (typeof window.renderScalePage === "function") window.renderScalePage();
      appendAssistLine("system", "Applied: fretboard refreshed from current root/scale/instrument (Confirmed).");
    });
    $("#assist_copy_ctx").on("click", function () {
      var json = JSON.stringify(getInstrumentContext(), null, 2);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(json).catch(function () {
          appendAssistLine("system", json);
        });
      } else {
        appendAssistLine("system", json);
      }
    });
    $("#assist_musicxml").on("click", function () {
      exportMusicXMLScaleSnapshot();
    });
    $("#assist_input").on("blur", saveAssistDraft);
    $("#assist_openai_save").on("click", function () {
      var k = $("#assist_openai_key").val() || "";
      callPyApi("set_openai_api_key", k)
        .then(function (r) {
          $("#assist_openai_key").val("");
          if (r === "offline_mode") {
            appendAssistLine("system", "Режим офлайн: ключ OpenAI не сохраняется.");
            return;
          }
          appendAssistLine("system", "Сессионный ключ OpenAI: " + (r || "ok") + " (память процесса).");
          refreshOpenaiConnectionFromHost();
        })
        .catch(function () {
          appendAssistLine("system", "Python API недоступен (нужен pywebview).");
        });
    });
    $("#assist_openai_clear").on("click", function () {
      $("#assist_openai_key").val("");
      callPyApi("set_openai_api_key", "")
        .then(function () {
          appendAssistLine("system", "Сессионный ключ OpenAI очищен.");
          refreshOpenaiConnectionFromHost();
        })
        .catch(function () {
          appendAssistLine("system", "Python API недоступен.");
        });
    });
    function doGptSend(t) {
      if (!t) return;
      appendAssistLine("user", t);
      var traceId = newTraceId();
      var payload = {
        user_text: t,
        include_context: $("#assist_openai_ctx").is(":checked"),
        context_json: getInstrumentContext(),
        client_trace_id: traceId
      };
      $("#assist_send").prop("disabled", true);
      logToHost("openai_chat_ui_send", { trace_id: traceId, include_context: payload.include_context });
      callPyApi("openai_chat", JSON.stringify(payload))
        .then(function (res) {
          var o = typeof res === "string" ? JSON.parse(res) : res;
          if (o.ok) {
            logToHost("openai_chat_ui_ok", { trace_id: traceId });
            appendAssistLine("gpt", (o.content || "").trim() || "(пустой ответ)");
          }
          else {
            logToHost("openai_chat_ui_err", { trace_id: traceId, error: o.error || "unknown" });
            appendAssistLine("gpt_error", formatGptErrorMessage(o.message || o.error || JSON.stringify(o)));
            if (o.error === "missing_api_key") refreshOpenaiConnectionFromHost();
          }
        })
        .catch(function (e) {
          logToHost("openai_chat_ui_exc", { trace_id: traceId, message: String(e && e.message ? e.message : e) });
          appendAssistLine("gpt_error", formatGptErrorMessage("Запрос не выполнен: " + (e && e.message ? e.message : String(e))));
        })
        .finally(function () {
          $("#assist_send").prop("disabled", false);
        });
      $("#assist_input").val("");
      saveAssistDraft();
    }

    $("#assist_send").on("click", function () {
      var t = ($("#assist_input").val() || "").trim();
      if (!t) return;
      var m = getSendMode();
      if (m === "draft") {
        doDraftSend(t);
        return;
      }
      // GPT mode
      if (!isAssistMode()) {
        appendAssistLine("system", "Режим офлайн: GPT отключён. Переключите режим приложения на Assist в настройках.");
        return;
      }
      if (!openaiBridgeAvailable()) {
        appendAssistLine("system", "GPT недоступен: нужен запуск через phrygian_app.py (pywebview).");
        return;
      }
      doGptSend(t);
    });

    $("#assist_input").on("keydown", function (e) {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        $("#assist_send").trigger("click");
      }
    });

    // initialize send mode on open
    setSendMode(getSendMode());
  }

  function refreshSettingsMdBridge() {
    var el = $("#settings_md_bridge");
    if (!el.length) return;
    if (!isAssistMode()) {
      el.text("В режиме assist можно писать лог диалога на диск через pywebview.");
      $("#settings_dialog_md").prop("disabled", true);
      return;
    }
    $("#settings_dialog_md").prop("disabled", false);
    el.text(
      pywebviewDialogMdCallable()
        ? ""
        : "Запись в Markdown работает только при запуске через phrygian_app.py (pywebview)."
    );
  }

  function openSettings() {
    $("#settings_backdrop").removeClass("hidden").attr("aria-hidden", "false");
    $("#settings_poly_mode").text(getPolyMode());
    syncSettingsModeRadios();
    $("#settings_poly_mode_bridge").text("");
    $("#settings_dialog_md").prop("checked", isDialogMdEnabled());
    $("#settings_gpt_ping_result").text("");
    refreshSettingsMdBridge();
    syncAssistOpenaiControls();
  }

  function closeSettings() {
    $("#settings_backdrop").addClass("hidden").attr("aria-hidden", "true");
  }

  function initSettingsHandlers() {
    $("#poly_settings_btn").on("click", function () {
      openSettings();
    });
    $("#settings_close").on("click", function () {
      closeSettings();
    });
    $("#settings_backdrop").on("click", function (e) {
      if (e.target === this) closeSettings();
    });
    $("#settings_dialog_md").on("change", function () {
      setDialogMdEnabled(this.checked);
      refreshSettingsMdBridge();
    });
    $("#settings_gpt_ping").on("click", function () {
      $("#settings_gpt_ping_result").text("Проверяю…");
      $("#settings_dot_openai").removeClass("ok bad");
      if (typeof window.pywebview.api.validate_openai_key !== "function") {
        $("#settings_gpt_ping_result").text("Нет API validate_openai_key.");
        return;
      }
      var k = $("#settings_openai_key").val() || "";
      callPyApi("validate_openai_key", JSON.stringify({ key: k }))
        .then(function (raw) {
          var o = typeof raw === "string" ? JSON.parse(raw) : raw;
          if (o.ok) {
            $("#settings_gpt_ping_result").text("OK (HTTP " + (o.http_status || 200) + ")");
            $("#settings_dot_openai").addClass("ok");
          } else {
            $("#settings_gpt_ping_result").text(String(o.message || o.error || JSON.stringify(o)).slice(0, 220));
            $("#settings_dot_openai").addClass("bad");
          }
        })
        .catch(function () {
          $("#settings_gpt_ping_result").text("Python API недоступен.");
          $("#settings_dot_openai").addClass("bad");
        });
    });
    $("#settings_openai_save").on("click", function () {
      var k = $("#settings_openai_key").val() || "";
      callPyApi("set_openai_api_key", k)
        .then(function (r) {
          $("#settings_openai_key").val("");
          if (r !== "offline_mode") refreshOpenaiConnectionFromHost();
        })
        .catch(function () {});
    });
    $("#settings_openai_clear").on("click", function () {
      $("#settings_openai_key").val("");
      callPyApi("set_openai_api_key", "")
        .then(function () {
          refreshOpenaiConnectionFromHost();
        })
        .catch(function () {});
    });

    $("#settings_claude_validate").on("click", function () {
      $("#settings_claude_validate_result").text("Проверяю…");
      $("#settings_dot_claude").removeClass("ok bad");
      if (typeof window.pywebview.api.validate_claude_key !== "function") {
        $("#settings_claude_validate_result").text("Нет API validate_claude_key.");
        $("#settings_dot_claude").addClass("bad");
        return;
      }
      var k = $("#settings_claude_key").val() || "";
      callPyApi("validate_claude_key", JSON.stringify({ key: k }))
        .then(function (raw) {
          var o = typeof raw === "string" ? JSON.parse(raw) : raw;
          if (o.ok) {
            $("#settings_claude_validate_result").text(o.message || "OK");
            $("#settings_dot_claude").addClass("ok");
          } else {
            $("#settings_claude_validate_result").text(String(o.message || o.error || JSON.stringify(o)).slice(0, 220));
            $("#settings_dot_claude").addClass("bad");
          }
        })
        .catch(function () {
          $("#settings_claude_validate_result").text("Python API недоступен.");
          $("#settings_dot_claude").addClass("bad");
        });
    });

    $("#settings_claude_save").on("click", function () {
      var k = $("#settings_claude_key").val() || "";
      callPyApi("set_claude_api_key", k)
        .then(function () {
          $("#settings_claude_key").val("");
        })
        .catch(function () {});
    });
    $("#settings_claude_clear").on("click", function () {
      $("#settings_claude_key").val("");
      callPyApi("set_claude_api_key", "")
        .then(function () {})
        .catch(function () {});
    });
    $("#settings_claude_copy").on("click", function () {
      var cmd = "python scripts/claude_terminal.py";
      var hint = $("#settings_claude_hint");
      var tryCopy = function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          return navigator.clipboard.writeText(text).then(function () {
            hint.text("Скопировано в буфер: " + text + "  (перед этим в терминале: claude login)");
          }).catch(function () {
            hint.text("Не удалось скопировать — выделите команду вручную: " + text);
          });
        }
        hint.text(text);
        return Promise.resolve();
      };

      // Prefer a fully-qualified "cd && python ..." for Windows users who run from arbitrary dirs.
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_repo_root === "function") {
        callPyApi("get_repo_root", "")
          .then(function (raw) {
            var o = typeof raw === "string" ? JSON.parse(raw) : raw;
            var root = o && o.root ? String(o.root) : "";
            if (o && o.ok && root) {
              var full = 'cd /d "' + root + '" && ' + cmd;
              return tryCopy(full);
            }
            return tryCopy(cmd);
          })
          .catch(function () {
            return tryCopy(cmd);
          });
        return;
      }
      tryCopy(cmd);
    });
    $("#settings_claude_openwin").on("click", function () {
      var hint = $("#settings_claude_hint");
      if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.launch_claude_terminal_window === "function")) {
        hint.text("Нет API launch_claude_terminal_window (нужно запустить через phrygian_app.py на Windows).");
        return;
      }
      callPyApi("launch_claude_terminal_window", "")
        .then(function (raw) {
          var o = typeof raw === "string" ? JSON.parse(raw) : raw;
          if (o && o.ok) hint.text("Открыл отдельное окно терминала (если Claude не залогинен — сначала: claude login).");
          else hint.text("Не удалось открыть терминал: " + String((o && (o.message || o.error)) || raw));
        })
        .catch(function (e) {
          hint.text("Не удалось открыть терминал: " + String(e && e.message ? e.message : e));
        });
    });
    $("#settings_assist_detach").on("click", function () {
      var bridge = $("#settings_poly_mode_bridge");
      if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_assist_window === "function")) {
        bridge.text("Нет API для отдельного окна (нужно запустить через phrygian_app.py).");
        return;
      }
      callPyApi("open_assist_window", "")
        .then(function (raw) {
          var o = typeof raw === "string" ? JSON.parse(raw) : raw;
          if (o && o.ok) bridge.text("Assist/GPT откреплены в отдельное окно.");
          else bridge.text("Не удалось открыть окно: " + String((o && (o.message || o.error)) || raw));
        })
        .catch(function () {
          bridge.text("Не удалось открыть окно (Python API недоступен).");
        });
    });
    $("#settings_windows_tile").on("click", function () {
      var bridge = $("#settings_poly_mode_bridge");
      if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.tile_windows === "function")) {
        bridge.text("Нет API tile_windows (нужно запустить через phrygian_app.py на Windows).");
        return;
      }
      var ensureAssistWin =
        window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_assist_window === "function"
          ? callPyApi("open_assist_window", "")
          : Promise.resolve();
      ensureAssistWin
        .catch(function () {})
        .then(function () {
          return callPyApi("tile_windows", JSON.stringify({ mode: "vertical" }));
        })
        .then(function (raw) {
          var o = typeof raw === "string" ? JSON.parse(raw) : raw;
          if (o && o.ok) bridge.text("Окна разложены 50/50.");
          else if (o && o.error === "missing_windows")
            bridge.text("Нужно открыть второе окно Assist (кнопка «Открепить Assist/GPT…»), затем тайлинг.");
          else bridge.text("Не удалось разложить окна: " + String((o && (o.message || o.error)) || raw));
        })
        .catch(function () {
          bridge.text("Не удалось разложить окна (Python API недоступен).");
        });
    });
    $("#settings_poly_mode_apply").on("click", function () {
      var v = $('input[name="settings_poly_mode_pick"]:checked').val();
      if (v === "offline" || v === "assist") applyPolyModeRuntime(v);
    });
  }

  function initChromeHandlers() {
    $("#poly_fs_btn").on("click", toggleFullscreen);
    $("#poly_layout_select").on("change", function () {
      applyLayoutClass(this.value);
    });
    $("#poly_fret_box_select").on("change", function () {
      persistFretBoxMode(this.value);
      applyFretBoxLayout();
    });
    $(document).on("change", "#poly_fingering_toggle", function () {
      applyFingeringHints();
    });
    $(document).on("change", "#string_visibility_ops input.poly_str_vis", function () {
      applyStringHideClasses();
      applyFingeringHints();
    });
    $("#app_instrument_select").on("change", function () {
      setTimeout(function () {
        rebuildStringVisibilityUi();
      }, 0);
    });
  }

  window.polyphonia = {
    getInstrumentContext: getInstrumentContext,
    exportMusicXMLScaleSnapshot: exportMusicXMLScaleSnapshot,
    exportSession: exportSession,
    openAssist: openAssist,
    setFullscreen: toggleFullscreen,
    getPolyMode: getPolyMode,
    isAssistMode: isAssistMode,
    openaiBridgeAvailable: openaiBridgeAvailable
  };

  function boot() {
    applyPolyModeClass();
    applyPolyViewClass();
    logToHost("boot", { poly_mode: getPolyMode(), poly_view: getPolyView() });
    initLayoutFromStorage();
    initFretBoxFromStorage();
    initAssistHandlers();
    initSettingsHandlers();
    initChromeHandlers();
    loadAssistDraft();
    syncAssistOpenaiControls();
    wrapRenderScalePage();
    afterRenderScalePage();
    try {
      if (getPolyView() === "assist") openAssist();
    } catch (e0) {}
  }

  if (window.jQuery) {
    window.jQuery(function () {
      setTimeout(boot, 0);
    });
  }
})();
