with open('main.py', 'r', encoding='utf-8-sig', errors='ignore') as file:
    content = file.read()

with open('main.py', 'w', encoding='utf-8') as file:
    file.write(content)

print("Removed BOM character from main.py") 