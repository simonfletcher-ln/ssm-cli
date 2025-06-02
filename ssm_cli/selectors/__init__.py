import ssm_cli.selectors.tui as tui
import ssm_cli.selectors.first as first
import ssm_cli.selectors.gui as gui

SELECTORS = {
    'tui': tui.select,
    'first': first.select,
    'gui': gui.select
}
