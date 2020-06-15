import os, sys, time

from src.argparse import parse_cl_args
from src.distprocs import DistProcs

# import hunter
# hunter.trace(module='DistProcs', action=hunter.CallPrinter)

def main():
    start_t = time.time()
    print('start running main...')
    args = parse_cl_args()
    print('[mylog][run.py][11]distprocs = DistProcs(args, args.tsc, args.mode) ...')
    distprocs = DistProcs(args, args.tsc, args.mode)
    print('[mylog][run.py][12] distprocs.run() ...')
    distprocs.run()
    print(args)
    print('...finish running main')
    print('run time '+str((time.time()-start_t)/60))

if __name__ == '__main__':
    main() 
