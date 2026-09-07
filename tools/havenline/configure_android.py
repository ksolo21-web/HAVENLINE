"""Configure a Godot editor's Android SDK without storing credentials in Git."""
import argparse, os, re, subprocess
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--sdk',required=True,type=Path);p.add_argument('--java',required=True,type=Path);p.add_argument('--godot',required=True,type=Path);args=p.parse_args()
config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'godot'
config.mkdir(parents=True,exist_ok=True)
settings=config/'editor_settings-4.7.tres'
key=config/'havenline-review.keystore'
if not key.exists():
    subprocess.run([str(args.java/'bin/keytool'),'-genkeypair','-keystore',str(key),'-storepass','android','-alias','androiddebugkey','-keypass','android','-dname','CN=Android Debug,O=Android,C=US','-keyalg','RSA','-keysize','2048','-validity','10000'],check=True)
values={'export/android/android_sdk_path':str(args.sdk.resolve()),'export/android/java_sdk_path':str(args.java.resolve()),'export/android/debug_keystore':str(key),'export/android/debug_keystore_user':'androiddebugkey','export/android/debug_keystore_pass':'android'}
text=settings.read_text() if settings.exists() else '[gd_resource type="EditorSettings" format=3]\n\n[resource]\n'
for k,v in values.items():
    line=k+'="'+v.replace('\\','/')+'"'
    text=re.sub('^'+re.escape(k)+r'\s*=.*$',lambda _:line,text,flags=re.M) if re.search('^'+re.escape(k)+r'\s*=',text,re.M) else text.rstrip()+'\n'+line+'\n'
settings.write_text(text)
print('Godot Android SDK and isolated development signing configured.')
