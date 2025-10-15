import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--package", dest="packagename", type=str, help="Имя анализируемого пакета")
parser.add_argument("--url", dest="url", type=str, help="URL-адрес репозитория или путь к файлу тестового репозитория")
parser.add_argument("--mode", dest="mode", type=str, choices=['local', 'remote'], default='remote',
                    help="Режим работы с тестовым репозиторием: local или remote")
parser.add_argument("--version", dest="version", type=str, help="Версия пакета (например, 1.2.3)")
parser.add_argument("--output", dest="output", type=str, choices=['tree', 'list'], default='tree',
                    help="Режим вывода зависимостей: 'tree' или 'list'")
parser.add_argument("--filter", dest="filter", type=str, help="Подстрока для фильтрации пакетов")

args = parser.parse_args()

errors = []
if not args.packagename:
    errors.append("Имя пакета (--package) обязательно")
if not args.url:
    errors.append("URL (--url) обязателен")
if args.version and not args.version.replace('.', '').isdigit():
    errors.append("Версия пакета (--version) должна быть в формате x.y.z")
if args.mode not in ['local', 'remote']:
    errors.append("--mode должно быть local или remote")
if args.output not in ['tree', 'list']:
    errors.append("--output должно быть tree или list")

if errors:
    print("Ошибки валидации:", file=sys.stderr)
    for e in errors:
        print(f" - {e}", file=sys.stderr)
    sys.exit(1)

print("Параметры приложения:")
print(f"packagename={args.packagename}")
print(f"url={args.url}")
print(f"mode={args.mode}")
print(f"version={args.version}")
print(f"output={args.output}")
print(f"filter={args.filter}")
