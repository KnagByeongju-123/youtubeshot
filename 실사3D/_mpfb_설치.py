# 준비.sh 가 부름: MPFB2 확장을 블렌더(bpy)에 설치
import bpy,sys
print("MPFB 설치",bpy.ops.extensions.package_install_files(filepath=sys.argv[1],repo='user_default',enable_on_install=True))
bpy.ops.wm.save_userpref()
