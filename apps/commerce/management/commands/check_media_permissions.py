"""Проверка: может ли Django записывать файлы в MEDIA_ROOT (admin upload)."""
from __future__ import annotations

import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Проверяет права на запись в MEDIA_ROOT и типичные подпапки каталога.'

    SUBDIRS = (
        'products',
        'manufacturers/logos',
        'manufacturers/hero',
        'manufacturers/features',
        'banners',
        'news',
    )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        self.stdout.write(f'MEDIA_ROOT: {media_root}')
        self.stdout.write(f'MEDIA_URL:  {settings.MEDIA_URL}')
        self.stdout.write(f'UID процесса: {os.getuid()}  GID: {os.getgid()}')

        if not os.path.isdir(media_root):
            self.stdout.write(self.style.ERROR(f'Папка не существует: {media_root}'))
            self._print_fix()
            return

        ok = self._check_dir(media_root)
        for sub in self.SUBDIRS:
            path = os.path.join(media_root, sub)
            os.makedirs(path, exist_ok=True)
            ok = self._check_dir(path, label=sub) and ok

        if ok:
            self.stdout.write(self.style.SUCCESS('Запись в MEDIA_ROOT возможна — загрузка в админке должна работать.'))
        else:
            self.stdout.write(self.style.ERROR('Нет прав на запись — см. команды исправления ниже.'))
            self._print_fix()

    def _check_dir(self, path: str, *, label: str | None = None) -> bool:
        title = label or path
        try:
            stat = os.stat(path)
            self.stdout.write(
                f'  {title}: uid={stat.st_uid} gid={stat.st_gid} mode={oct(stat.st_mode & 0o777)}',
            )
            fd, tmp = tempfile.mkstemp(dir=path, prefix='._perm_test_')
            os.close(fd)
            os.remove(tmp)
            self.stdout.write(self.style.SUCCESS(f'    OK — запись в {title}'))
            return True
        except OSError as exc:
            self.stdout.write(self.style.ERROR(f'    FAIL — {title}: {exc}'))
            return False

    def _print_fix(self) -> None:
        media = settings.MEDIA_ROOT
        self.stdout.write('')
        self.stdout.write('Исправление на сервере (подставьте пользователя gunicorn, обычно www-data):')
        self.stdout.write(f'  sudo mkdir -p {media}/{{products,manufacturers,banners,news}}')
        self.stdout.write(f'  sudo chown -R www-data:www-data {media}')
        self.stdout.write(f'  sudo chmod -R 775 {media}')
        self.stdout.write('  sudo systemctl restart gunicorn')
