"""Một hàm xử lý cho mỗi lệnh CLI: lấy tham số -> gọi API package -> in JSON. Không có logic nghiệp vụ.

Import module feature bên trong hàm: main() phải đặt env AEDT (aedt_env.ensure) TRƯỚC mọi import pyedb / pyaedt.
Trả None (= 0) hoặc mã thoát.
"""
from .. import aedt_env
from ..core.errors import CopilotInputError
from .io import input_error, json_args, log, print_json


def _items(s):
    return [x for x in s.split(",") if x] or None


def inspect(a):
    from ..cut_board import inspect_board
    print_json({**inspect_board.inspect(a.board, a.cell), "aedt": aedt_env.info()})   # in SAU khi EDB đóng












def finish(a):
    from ..cut_board import aedt_finish
    print_json(aedt_finish.finish(a.aedb, a.port, a.design))




def pidc(a):
    from ..pi_dc import workflow
    print_json(workflow.run(a.dir, a.sim, [s for s in a.skills.split(",") if s] or None, a.skip_export, log))


def pidc_export(a):
    from ..pi_dc import export
    print_json(export.export(a.dir, a.sim, log=log, voltage_only=a.voltage_only))


def pidc_skill(a):
    from ..pi_dc import workflow
    kw = {"voltage": a.pt_voltage, "current": a.pt_current} if a.name == "power_tree" else {}
    r = workflow.run_skill(a.dir, a.name, a.sim, log, **kw)
    print_json({k: r[k] for k in ("skill", "verdict", "counts", "seconds")})


def pidc_report(a):
    from ..pi_dc import report as R
    print_json(R.build(a.dir, a.sim))


def layout_region(a):
    from ..edit_layout import run as LE
    print_json({**LE.region(a.board, a.box, _items(a.layers), _items(a.nets), a.cell, log=log),
                "aedt": aedt_env.info()})


def layout_edit(a):
    from ..edit_layout import run as LE
    print_json(LE.edit(a.plan, log=log))


def _json_op(call, a):
    """isim / design / catalog: --op + JSON -> API; lỗi đầu vào -> JSON {ok: false, ...}, mã 2."""
    try:
        print_json(call(a.op, json_args(a)))
    except CopilotInputError as ex:
        print_json(input_error(ex))
        return 2


def isim(a):
    from ..interface_sim import api
    return _json_op(api.call, a)


def design(a):
    from .. import design_tools
    return _json_op(design_tools.call, a)


def catalog(a):
    from ..catalog import api
    return _json_op(api.call, a)


def review_measure(a):
    from .. import review_checks
    try:
        out = review_checks.measure_report(a.board, a.channels, a.checks or None, a.cell, a.html, log=log,
                                           snapshot=a.snapshot)
    except CopilotInputError as ex:
        print_json(input_error(ex))
        return 2
    print_json(out)






def review_rules(a):
    """031: luật review (steering + code): list / get / enable / disable / guide-list."""
    from ..review_checks import _rules
    return _json_op(_rules.run_op, a)


def stackup_table(a):
    """030: bảng width / gap theo lớp từ stackup nhà máy (tool review_stackup_table)."""
    from ..review_checks import _stackup
    return _json_op(_stackup.run_op, a)


def snapshot(a):
    from ..layout_snapshot import api
    return _json_op(lambda op, args: api.run_op(op, args, log=log), a)


def config_serve(a):
    """040: local save service of config.html (started detached by isim_config)."""
    from ..interface_sim.config import serve
    return serve.main(a.port)


COMMANDS = {
    "inspect": inspect, "finish": finish,
    "pidc": pidc, "pidc-export": pidc_export, "pidc-skill": pidc_skill, "pidc-report": pidc_report,
    "layout-region": layout_region, "layout-edit": layout_edit,
    "isim": isim, "design": design, "review-measure": review_measure, "catalog": catalog,
    "snapshot": snapshot,
    "stackup-table": stackup_table,
    "review-rules": review_rules,
    "config-serve": config_serve,
}
