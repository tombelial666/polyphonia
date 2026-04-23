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
  var STORAGE_ASSIST_GOAL_MODE = "polyphonia_assist_goal_mode";
  var STORAGE_UI_ZOOM = "polyphonia_ui_zoom";
  var STORAGE_ASSIST_THREAD_ACTIVE = "polyphonia_assist_thread_active_";
  var STORAGE_ASSIST_TRANSCRIPT = "polyphonia_assist_transcript_";
  var lastStringCount = null;
  var assistState = {
    keyId: "",
    threadId: "",
    messages: []
  };

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
      var qv = (u.searchParams.get("poly_view") || "").toLowerCase();
      if (qv) return qv;
      var h = (u.hash || "").replace(/^#/, "");
      if (h.indexOf("poly_view=") === 0) return h.slice("poly_view=".length).split(/[&?]/)[0].toLowerCase();
      var m = h.match(/(?:^|&)poly_view=([^&]+)/);
      if (m && m[1]) return decodeURIComponent(m[1]).toLowerCase();
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

  function buildScaleContext() {
    var out = {
      rootCode: $("#note").val() || "",
      scaleCode: $("#scale").val() || "",
      rootKey: null,
      scaleName: "",
      scaleNoteKeys: [],
      scaleNoteNames: []
    };
    try {
      if (typeof window.getCurrentRootKey === "function") {
        out.rootKey = window.getCurrentRootKey();
      }
      if (typeof window.getScaleByCode === "function") {
        var scaleInfo = window.getScaleByCode(out.scaleCode);
        if (scaleInfo && scaleInfo.length >= 3) {
          out.scaleName = String(scaleInfo[2] || "");
          var scaleIntervals = Array.isArray(scaleInfo[1]) ? scaleInfo[1] : [];
          if (typeof out.rootKey === "number" && out.rootKey >= 0) {
            out.scaleNoteKeys = scaleIntervals.map(function (step) {
              return (((Number(step) || 0) + out.rootKey) % 12 + 12) % 12;
            });
            if (window.Note && typeof window.Note.getNote === "function") {
              out.scaleNoteNames = out.scaleNoteKeys.map(function (k) {
                return window.Note.getNote(k);
              });
            }
          }
        }
      }
      if (window.Note && typeof window.Note.getNote === "function" && typeof out.rootKey === "number" && out.rootKey >= 0) {
        out.rootName = window.Note.getNote(out.rootKey);
      } else {
        out.rootName = "";
      }
    } catch (e0) {}
    return out;
  }

  function buildSelectedChordContext() {
    try {
      var st = window.currentChordState || null;
      if (!st || typeof st.chordIndex !== "number" || typeof st.rootKey !== "number") return null;
      var chordArr = window.allChordAr || [];
      var chordInfo = chordArr[st.chordIndex];
      if (!chordInfo) return null;
      var ints = Array.isArray(chordInfo[1]) ? chordInfo[1] : [];
      var chordNoteKeys = ints.map(function (step) {
        return (((Number(step) || 0) + st.rootKey) % 12 + 12) % 12;
      });
      var chordNoteNames = chordNoteKeys.map(function (k) {
        if (window.Note && typeof window.Note.getNote === "function") return window.Note.getNote(k);
        return String(k);
      });
      return {
        chordIndex: st.chordIndex,
        rootKey: st.rootKey,
        chordCode: chordInfo[0] || "",
        chordName: (window.Note && typeof window.Note.getNote === "function" ? window.Note.getNote(st.rootKey) + " " : "") + (chordInfo[2] || ""),
        chordDegrees: chordInfo[3] || "",
        chordAbbrev: chordInfo[4] || "",
        chordNoteKeys: chordNoteKeys,
        chordNoteNames: chordNoteNames
      };
    } catch (e1) {
      return null;
    }
  }

  function getInstrumentContext() {
    var ctx = {
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
      riffDraft: window.__poly_riff_draft || null,
      scaleContext: buildScaleContext(),
      selectedChord: buildSelectedChordContext()
    };
    try {
      if (window.instrumentInfo && typeof window.getCurrentTuning === "function") {
        var tn = window.getCurrentTuning(window.instrumentInfo) || [];
        ctx.tuningResolved = Array.isArray(tn) ? tn.slice() : [];
      } else {
        ctx.tuningResolved = [];
      }
    } catch (e2) {
      ctx.tuningResolved = [];
    }
    return ctx;
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
        try {
          if (o && o.persisted) line += " (на диске: сохранён локально)";
        } catch (e0) {}
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
      $("#assist_openai_save, #assist_openai_clear, #assist_openai_forget, #assist_ask_gpt, #assist_openai_key, #assist_openai_remember").prop("disabled", true);
      $("#assist_openai_status").text("");
      $("#assist_openai_summary").text("");
      ensureThreadControlsEnabled(false, "");
      $("#settings_openai_key, #settings_openai_save, #settings_openai_clear, #settings_openai_forget, #settings_gpt_ping, #settings_openai_remember").prop("disabled", true);
      $("#settings_claude_key, #settings_claude_save, #settings_claude_clear, #settings_claude_validate").prop(
        "disabled",
        true
      );
      $("#settings_gpt_line").text("GPT в UI доступен в режиме assist.");
      $("#settings_gpt_model").text("");
      return;
    }
    var on = pywebviewOpenaiCallable();
    $("#assist_openai_save, #assist_openai_clear, #assist_openai_forget, #assist_ask_gpt, #assist_openai_key, #assist_openai_remember").prop("disabled", !on);
    ensureThreadControlsEnabled(on, on ? "" : "Нет моста pywebview: треды из Python недоступны.");
    $("#settings_openai_key, #settings_openai_save, #settings_openai_clear, #settings_openai_forget, #settings_gpt_ping, #settings_openai_remember").prop("disabled", !on);
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

  function applySplitTwoBandsClass(splitOn) {
    var $disp = $("#stringed_display");
    if (!$disp.length) return;
    $disp.removeClass("poly_split_2bands");
    $disp.find(".poly_split_lower").removeClass("poly_split_lower");
    if (!splitOn) return;
    var total = window.instrumentInfo && window.instrumentInfo.notes ? window.instrumentInfo.notes.length : 0;
    if (!total || total < 4) return;
    var lowerLimit = Math.floor(total / 2);
    for (var s = 0; s < lowerLimit; s++) {
      $disp.find(".s_" + s).addClass("poly_split_lower");
      $disp.find("#string_" + s).addClass("poly_split_lower");
      $disp.find("#string_label_" + s).addClass("poly_split_lower");
    }
    $disp.addClass("poly_split_2bands");
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
      $disp.removeClass("poly_fret_boxes poly_fb_mode_3 poly_fb_mode_32 poly_split_2bands");
      return;
    }
    var mode = ($("#poly_fret_box_select").val() || "fret_box_off");
    var splitBands = mode === "fret_box_split_3" || mode === "fret_box_split_32";
    var baseMode = mode;
    if (mode === "fret_box_split_3") baseMode = "fret_box_3";
    if (mode === "fret_box_split_32") baseMode = "fret_box_32";
    $disp.removeClass("poly_fret_boxes poly_fb_mode_3 poly_fb_mode_32 poly_split_2bands");
    applySplitTwoBandsClass(splitBands);
    if (mode === "fret_box_off") return;
    $disp.addClass("poly_fret_boxes");
    if (baseMode === "fret_box_3") $disp.addClass("poly_fb_mode_3");
    else if (baseMode === "fret_box_32") $disp.addClass("poly_fb_mode_32");
    var capo = parseInt($("#capo_fret").val() || "0", 10) || 0;

    function markCol(fid, fretNum) {
      var $nc = $("#" + fid);
      var $fc = $("#fret_" + fretNum);
      if (!$nc.length) return;
      var g;
      var isStart = false;
      if (baseMode === "fret_box_3") {
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

  function readUiZoom() {
    var z = 1;
    try {
      z = parseFloat(localStorage.getItem(STORAGE_UI_ZOOM) || "1");
    } catch (e0) {}
    if (!isFinite(z)) z = 1;
    if (z < 0.7) z = 0.7;
    if (z > 1.6) z = 1.6;
    return z;
  }

  function applyUiZoom(z) {
    var nz = Number(z || 1);
    if (!isFinite(nz)) nz = 1;
    if (nz < 0.7) nz = 0.7;
    if (nz > 1.6) nz = 1.6;
    var v = String(Math.round(nz * 100) / 100);
    document.documentElement.style.zoom = v;
    try {
      localStorage.setItem(STORAGE_UI_ZOOM, v);
    } catch (e0) {}
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

  function activeThreadStorageKey(keyId) {
    return STORAGE_ASSIST_THREAD_ACTIVE + (keyId || "none");
  }

  function transcriptStorageKey(keyId, threadId) {
    return STORAGE_ASSIST_TRANSCRIPT + (keyId || "none") + "_" + (threadId || "default");
  }

  function loadCachedTranscript(keyId, threadId) {
    try {
      var raw = localStorage.getItem(transcriptStorageKey(keyId, threadId));
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e0) {
      return [];
    }
  }

  function persistTranscriptCache() {
    try {
      var rows = assistState.messages || [];
      var cut = rows.slice(-200);
      localStorage.setItem(transcriptStorageKey(assistState.keyId, assistState.threadId), JSON.stringify(cut));
    } catch (e0) {}
  }

  function clearAssistMessagesUi() {
    $("#assist_messages").empty();
  }

  function appendAssistLine(role, text, opts) {
    opts = opts || {};
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
    if (!opts.skipState) {
      assistState.messages.push({ role: role, text: text, ts: new Date().toISOString() });
      if (assistState.messages.length > 300) assistState.messages = assistState.messages.slice(-300);
      persistTranscriptCache();
    }
    if (!opts.skipPersistMd) persistAssistDialogMd(role, text);
  }

  function setAssistTranscript(rows, options) {
    options = options || {};
    clearAssistMessagesUi();
    assistState.messages = [];
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var role = String(row.role || "system");
      var text = String(row.text || "");
      if (!text) continue;
      appendAssistLine(role, text, { skipPersistMd: true });
    }
    if (!options.skipCache) persistTranscriptCache();
  }

  function setActiveThreadId(keyId, threadId) {
    try {
      localStorage.setItem(activeThreadStorageKey(keyId), threadId || "default");
    } catch (e0) {}
  }

  function getActiveThreadId(keyId) {
    try {
      return localStorage.getItem(activeThreadStorageKey(keyId)) || "";
    } catch (e0) {
      return "";
    }
  }

  function renderThreadOptions(threads) {
    var sel = $("#assist_thread_select");
    if (!sel.length) return;
    sel.empty();
    for (var i = 0; i < threads.length; i++) {
      var t = threads[i];
      var title = String(t.title || "").trim();
      var label = title ? title : "Чат " + (i + 1);
      var op = $("<option></option>").attr("value", String(t.thread_id || "")).text(label.slice(0, 96));
      sel.append(op);
    }
    if (assistState.threadId) sel.val(assistState.threadId);
  }

  function ensureThreadControlsEnabled(on, hint) {
    $("#assist_thread_select, #assist_thread_new").prop("disabled", !on);
    if (typeof hint === "string") $("#assist_thread_hint").text(hint);
  }

  function listThreadsFromHost() {
    if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.list_openai_threads !== "function") {
      return Promise.resolve({ ok: false, error: "no_threads_api" });
    }
    return callPyApi("list_openai_threads", JSON.stringify({ key_id: assistState.keyId }))
      .then(function (raw) {
        return typeof raw === "string" ? JSON.parse(raw) : raw;
      });
  }

  function loadThreadFromHost(threadId) {
    if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.load_openai_thread !== "function") {
      return Promise.resolve({ ok: false, error: "no_load_api" });
    }
    return callPyApi(
      "load_openai_thread",
      JSON.stringify({ key_id: assistState.keyId, thread_id: threadId, limit: 240 })
    ).then(function (raw) {
      return typeof raw === "string" ? JSON.parse(raw) : raw;
    });
  }

  function ensureOpenAiIdentity() {
    if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_openai_identity === "function")) {
      assistState.keyId = "no_pywebview";
      return Promise.resolve({ ok: false, error: "no_identity_api", key_id: assistState.keyId });
    }
    return callPyApi("get_openai_identity", "")
      .then(function (raw) {
        var o = typeof raw === "string" ? JSON.parse(raw) : raw;
        assistState.keyId = String((o && o.key_id) || "").trim();
        return o;
      });
  }

  function createNewThreadOnHost() {
    if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.new_openai_thread === "function")) {
      return Promise.resolve({ ok: false, error: "no_new_thread_api" });
    }
    return callPyApi("new_openai_thread", JSON.stringify({ key_id: assistState.keyId }))
      .then(function (raw) {
        return typeof raw === "string" ? JSON.parse(raw) : raw;
      });
  }

  function switchToThread(threadId, opts) {
    opts = opts || {};
    assistState.threadId = String(threadId || "default");
    setActiveThreadId(assistState.keyId, assistState.threadId);
    $("#assist_thread_select").val(assistState.threadId);
    return loadThreadFromHost(assistState.threadId)
      .then(function (o) {
        if (o && o.ok && Array.isArray(o.messages)) {
          setAssistTranscript(o.messages);
          $("#assist_thread_hint").text("Тред загружен.");
        } else {
          var cached = loadCachedTranscript(assistState.keyId, assistState.threadId);
          setAssistTranscript(cached, { skipCache: true });
          if (!opts.quiet) $("#assist_thread_hint").text("Тред не удалось прочитать с диска, показан локальный кэш.");
        }
      })
      .catch(function () {
        var cached = loadCachedTranscript(assistState.keyId, assistState.threadId);
        setAssistTranscript(cached, { skipCache: true });
        if (!opts.quiet) $("#assist_thread_hint").text("Ошибка чтения треда, показан локальный кэш.");
      });
  }

  function initAssistThreading() {
    if (!isAssistMode()) return Promise.resolve();
    return ensureOpenAiIdentity()
      .then(function (ident) {
        if (!ident || !ident.ok || !assistState.keyId) {
          assistState.keyId = assistState.keyId || "no_key";
          assistState.threadId = getActiveThreadId(assistState.keyId) || "local";
          var cached = loadCachedTranscript(assistState.keyId, assistState.threadId);
          setAssistTranscript(cached, { skipCache: true });
          ensureThreadControlsEnabled(false, "Нет активного ключа OpenAI: история доступна только как локальный кэш этого окна.");
          return;
        }
        ensureThreadControlsEnabled(true, "");
        return listThreadsFromHost()
          .then(function (o) {
            var threads = (o && o.ok && Array.isArray(o.threads)) ? o.threads : [];
            if (!threads.length) {
              return createNewThreadOnHost().then(function (created) {
                if (created && created.ok && created.thread_id) {
                  threads = [{ thread_id: created.thread_id, title: "" }];
                }
                return threads;
              });
            }
            return threads;
          })
          .then(function (threads) {
            threads = threads || [];
            if (!threads.length) {
              ensureThreadControlsEnabled(false, "Не удалось инициализировать треды.");
              return;
            }
            renderThreadOptions(threads);
            var active = getActiveThreadId(assistState.keyId);
            var found = false;
            for (var i = 0; i < threads.length; i++) {
              if (String(threads[i].thread_id) === active) {
                found = true;
                break;
              }
            }
            assistState.threadId = found ? active : String(threads[0].thread_id || "default");
            setActiveThreadId(assistState.keyId, assistState.threadId);
            return switchToThread(assistState.threadId, { quiet: true });
          });
      })
      .catch(function () {
        assistState.keyId = "no_pywebview";
        assistState.threadId = getActiveThreadId(assistState.keyId) || "local";
        var cached = loadCachedTranscript(assistState.keyId, assistState.threadId);
        setAssistTranscript(cached, { skipCache: true });
        ensureThreadControlsEnabled(false, "Python API недоступен: показан только локальный кэш.");
      });
  }

  function formatGptErrorMessage(raw) {
    var s = String(raw || "").trim();
    if (!s) return "Ошибка GPT.";
    try {
      var o = JSON.parse(s);
      if (o && o.error && (o.error.message || o.error.type || o.error.code)) {
        var msg = String(o.error.message || "Ошибка").trim();
        var code = String(o.error.code || o.error.type || "").trim();
        if (code === "insufficient_quota") {
          return "OpenAI отклонил запрос: исчерпана квота/биллинг для ключа (" + code + "). Проверьте план и billing, затем повторите.";
        }
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
    initAssistThreading();
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
    if (
      fb !== "fret_box_off" &&
      fb !== "fret_box_3" &&
      fb !== "fret_box_32" &&
      fb !== "fret_box_split_3" &&
      fb !== "fret_box_split_32"
    ) fb = "fret_box_off";
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

    function setGoalMode(mode) {
      var v = String(mode || "auto").toLowerCase();
      if (["auto", "compose", "theory", "production", "practice", "analysis"].indexOf(v) < 0) v = "auto";
      try {
        localStorage.setItem(STORAGE_ASSIST_GOAL_MODE, v);
      } catch (e0) {}
      $("#assist_goal_mode").val(v);
      var map = {
        auto: "Auto",
        compose: "Composer",
        theory: "Theory",
        production: "Production",
        practice: "Practice",
        analysis: "Analyze"
      };
      $("#assist_mode_badge").text("Mode: " + (map[v] || "Auto"));
    }

    function getGoalMode() {
      var v = "auto";
      try {
        v = localStorage.getItem(STORAGE_ASSIST_GOAL_MODE) || v;
      } catch (e0) {}
      v = String(v || "auto").toLowerCase();
      if (["auto", "compose", "theory", "production", "practice", "analysis"].indexOf(v) < 0) return "auto";
      return v;
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
    $("#assist_goal_mode").on("change", function () {
      setGoalMode(this.value);
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
    $("#assist_copy_last").on("click", function () {
      var rows = assistState.messages || [];
      var target = null;
      for (var i = rows.length - 1; i >= 0; i--) {
        if (rows[i] && (rows[i].role === "gpt" || rows[i].role === "assistant" || rows[i].role === "gpt_error")) {
          target = String(rows[i].text || "");
          break;
        }
      }
      if (!target) {
        appendAssistLine("system", "Пока нечего копировать: нет ответа GPT в текущем чате.");
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(target).then(function () {
          appendAssistLine("system", "Последний ответ скопирован.");
        }).catch(function () {
          appendAssistLine("system", target);
        });
      } else {
        appendAssistLine("system", target);
      }
    });
    $("#assist_copy_chat").on("click", function () {
      var rows = assistState.messages || [];
      if (!rows.length) {
        appendAssistLine("system", "Текущий чат пуст.");
        return;
      }
      var text = rows.map(function (r) {
        return "[" + String(r.role || "system") + "] " + String(r.text || "");
      }).join("\n\n");
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          appendAssistLine("system", "Текст чата скопирован.");
        }).catch(function () {
          appendAssistLine("system", text.slice(0, 5000));
        });
      } else {
        appendAssistLine("system", text.slice(0, 5000));
      }
    });
    $("#assist_musicxml").on("click", function () {
      exportMusicXMLScaleSnapshot();
    });
    $("#assist_input").on("blur", saveAssistDraft);
    $("#assist_openai_save").on("click", function () {
      var k = $("#assist_openai_key").val() || "";
      var remember = !!$("#assist_openai_remember").is(":checked");
      var method =
        window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_openai_api_key_persist === "function"
          ? "set_openai_api_key_persist"
          : "set_openai_api_key";
      var arg = method === "set_openai_api_key_persist" ? JSON.stringify({ key: k, remember: remember }) : k;
      callPyApi(method, arg)
        .then(function (r) {
          $("#assist_openai_key").val("");
          if (r === "offline_mode") {
            appendAssistLine("system", "Режим офлайн: ключ OpenAI не сохраняется.");
            return;
          }
          try {
            if (typeof r === "string" && r.trim().indexOf("{") === 0) r = JSON.parse(r);
          } catch (e0) {}
          var status = typeof r === "string" ? r : (r && r.status ? r.status : "ok");
          var remembered = !!(r && r.remembered);
          appendAssistLine(
            "system",
            "Сессионный ключ OpenAI: " + status + " (память процесса)" + (remembered ? " + сохранён локально." : ".")
          );
          refreshOpenaiConnectionFromHost();
          initAssistThreading();
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
          initAssistThreading();
        })
        .catch(function () {
          appendAssistLine("system", "Python API недоступен.");
        });
    });
    $("#assist_openai_forget").on("click", function () {
      if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.forget_openai_api_key_persisted === "function")) {
        appendAssistLine("system", "Нет API для «Забыть» (нужен обновлённый phrygian_app.py).");
        return;
      }
      callPyApi("forget_openai_api_key_persisted", "")
        .then(function () {
          appendAssistLine("system", "Сохранённый ключ OpenAI удалён с диска (Confirmed).");
          refreshOpenaiConnectionFromHost();
        })
        .catch(function () {
          appendAssistLine("system", "Не удалось удалить сохранённый ключ.");
        });
    });
    $("#assist_thread_select").on("change", function () {
      var threadId = String($(this).val() || "");
      if (!threadId) return;
      switchToThread(threadId);
    });
    $("#assist_thread_new").on("click", function () {
      if (!assistState.keyId) {
        $("#assist_thread_hint").text("Нет key_id для создания нового чата.");
        return;
      }
      createNewThreadOnHost()
        .then(function (o) {
          if (!(o && o.ok && o.thread_id)) {
            $("#assist_thread_hint").text("Не удалось создать новый чат.");
            return;
          }
          return listThreadsFromHost().then(function (lst) {
            var threads = (lst && lst.ok && Array.isArray(lst.threads)) ? lst.threads : [];
            renderThreadOptions(threads);
            assistState.threadId = String(o.thread_id);
            setActiveThreadId(assistState.keyId, assistState.threadId);
            return switchToThread(assistState.threadId);
          });
        })
        .catch(function () {
          $("#assist_thread_hint").text("Ошибка при создании чата.");
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
        client_trace_id: traceId,
        thread_id: assistState.threadId || "default",
        key_id: assistState.keyId || "",
        goal_mode: getGoalMode()
      };
      $("#assist_send").prop("disabled", true);
      logToHost("openai_chat_ui_send", { trace_id: traceId, include_context: payload.include_context });
      callPyApi("openai_chat", JSON.stringify(payload))
        .then(function (res) {
          var o = typeof res === "string" ? JSON.parse(res) : res;
          if (o.ok) {
            logToHost("openai_chat_ui_ok", { trace_id: traceId });
            appendAssistLine("gpt", (o.content || "").trim() || "(пустой ответ)");
            if (o.thread_id) {
              assistState.threadId = String(o.thread_id);
              setActiveThreadId(assistState.keyId, assistState.threadId);
              $("#assist_thread_select").val(assistState.threadId);
            }
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
      initAssistThreading()
        .then(function () {
          doGptSend(t);
        })
        .catch(function () {
          doGptSend(t);
        });
    });

    $("#assist_input").on("keydown", function (e) {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        $("#assist_send").trigger("click");
      }
    });

    // initialize send mode on open
    setSendMode(getSendMode());
    setGoalMode(getGoalMode());
    initAssistThreading();
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
      var remember = !!$("#settings_openai_remember").is(":checked");
      var method =
        window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_openai_api_key_persist === "function"
          ? "set_openai_api_key_persist"
          : "set_openai_api_key";
      var arg = method === "set_openai_api_key_persist" ? JSON.stringify({ key: k, remember: remember }) : k;
      callPyApi(method, arg)
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
    $("#settings_openai_forget").on("click", function () {
      if (!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.forget_openai_api_key_persisted === "function")) {
        $("#settings_gpt_ping_result").text("Нет API forget_openai_api_key_persisted (нужен обновлённый phrygian_app.py).");
        return;
      }
      callPyApi("forget_openai_api_key_persisted", "")
        .then(function () {
          $("#settings_gpt_ping_result").text("Сохранённый ключ удалён с диска.");
          refreshOpenaiConnectionFromHost();
        })
        .catch(function () {
          $("#settings_gpt_ping_result").text("Не удалось удалить сохранённый ключ.");
        });
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
    $(document).on("keydown", function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      var key = String(e.key || "").toLowerCase();
      if (key === "+" || key === "=" || key === "add") {
        e.preventDefault();
        applyUiZoom(readUiZoom() + 0.1);
        return;
      }
      if (key === "-" || key === "_" || key === "subtract") {
        e.preventDefault();
        applyUiZoom(readUiZoom() - 0.1);
        return;
      }
      if (key === "0") {
        e.preventDefault();
        applyUiZoom(1);
      }
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
    applyUiZoom(readUiZoom());
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
