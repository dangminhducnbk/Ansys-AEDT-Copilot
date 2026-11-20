# Implementation Plan: config page traces in top / 3D views + slider fill (044)

**Branch**: `main` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md) | Release 5.5.0 (minor: new page data)

## Summary

| Area | Change |
|---|---|
| `config/data.end_traces(paths, layer, frame_mm, pad_boxes=None)` | placement layer: as 5.3.0 (`layer`, `inner: false`). Other layers: path kept when one of its two END points lies in a signal pad box of the end (+ 0.02 mm) — via in pad / through-hole pin —, entry `{net, w_mm, pts, layer, inner: true, via: [x, y]}` (the end point in the pad). Same frame test, arc markers dropped, 400 per end in total. |
| `config/data.ends_data` | passes the signal pad boxes (mm) of the end. |
| `page.js` `topStatic` | inner traces dashed (`stroke-dasharray`), width 0.7 × w, colour per layer (`TRACE_LAYER_COLS` by first appearance of the layer over both ends of the channel); placement traces unchanged. |
| `page.js` legend | after "Trace": one entry per inner layer drawn ("Trace <layer>", dashed swatch). |
| `page.js` `draw3d` | inner traces dashed on z = −0.06 × span, then the board drawn semi-transparent over them, placement traces on z = 0 (before the pads), vertical dashed segment at each `via` from z = 0 down to the inner plane. |
| `page.js` slider | `--rr` = pct / 100 in the markup and in `cmPort` (fill follows the thumb). |

## Constitution Check

Gates / data safety / defaults / build: unchanged (page drawing + read-only data). Old pages (no `layer` key) draw as
5.3.0.

## Tests

`tests/unit/test_config_traces_044.py`: end_traces (placement kept, inner with end in pad kept + `via`, inner not
touching a pad dropped, frame test, arc markers, limit); page.js contains the `--rr` update in `cmPort` and the markup
(text check, as other page tests). Browser on copies: BOARDA request copy (J25 inner traces, 3D), board1 (slider).
