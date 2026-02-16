# Maintainer: Saeed Badrelden <helwanlinux@gmail.com>
pkgname=hel-netfix
pkgver=1.0
pkgrel=2
pkgdesc="Helwan Linux Network Repair GUI Tool (PyQt5)"
arch=('any')
url="https://github.com/helwan-linux/helwan-netfix"
license=('GPL3')
depends=('python' 'python-pyqt5')
makedepends=('git')
source=("git+$url.git")
md5sums=('SKIP')

package() {
  cd "$srcdir/helwan-netfix/hel-netFix"

  # تثبيت ملفات البرنامج داخل /usr/share
  install -d "$pkgdir/usr/share/$pkgname"
  cp -r . "$pkgdir/usr/share/$pkgname"

  # إنشاء اختصار في /usr/bin
  install -d "$pkgdir/usr/bin"
  echo -e "#!/bin/bash\npython3 /usr/share/$pkgname/hel_netfix_gui_qt.py" > "$pkgdir/usr/bin/$pkgname"
  chmod +x "$pkgdir/usr/bin/$pkgname"

  # تثبيت ملف .desktop
  install -d "$pkgdir/usr/share/applications"
  install -m644 "$srcdir/helwan-netfix/hel-netFix/hel-netfix.desktop" "$pkgdir/usr/share/applications/"

  # تثبيت الأيقونة (لو موجودة)
  if [[ -f "$srcdir/helwan-netfix/hel-netFix/netfix.png" ]]; then
    install -d "$pkgdir/usr/share/pixmaps"
    install -m644 "$srcdir/helwan-netfix/hel-netFix/netfix.png" "$pkgdir/usr/share/pixmaps/hel-netfix.png"
  fi
}
