#!/usr/bin/env python3
import os,subprocess,sys
if __name__=='__main__':
 port=os.getenv('PORT','5001'); args=[sys.executable,'manage.py']
 if len(sys.argv)>1 and sys.argv[1]=='init-db':args+=['migrate']
 else:args+=['runserver',f'0.0.0.0:{port}']
 raise SystemExit(subprocess.call(args))
