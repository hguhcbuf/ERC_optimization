"""Explicit CLI runner. Importing this module does not connect or move hardware."""
import argparse
from PLC_motion_controller_mod import initiate, run_gcode, close


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--file', default='set_height.nc')
    p.add_argument('--use-q1', action='store_true')
    p.add_argument('--allow-xyz-init', action='store_true')
    p.add_argument('--timeout', type=float, default=600.0)
    args = p.parse_args(argv)
    print(f'Execute PLC-side file: {args.file}; Q1={args.use_q1}')
    if input('Type RUN to execute: ').strip() != 'RUN':
        return 0
    if not initiate():
        return 1
    try:
        run_gcode(args.file, use_q1=args.use_q1,
                  allow_xyz_init=args.allow_xyz_init, timeout=args.timeout)
        return 0
    finally:
        close()


if __name__ == '__main__':
    raise SystemExit(main())
