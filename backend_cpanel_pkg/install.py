import subprocess, sys
print('Installing requirements...')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
print('ALL REQUIREMENTS INSTALLED SUCCESSFULLY!')
