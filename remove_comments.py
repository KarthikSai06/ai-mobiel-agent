import os
import tokenize

def remove_comments_from_file(filename):
    with open(filename, 'rb') as f:
        tokens = list(tokenize.tokenize(f.readline))
    
    out_tokens = []
    # Drop tokenize.COMMENT
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            continue
        out_tokens.append(tok)
        
    with open(filename, 'wb') as f:
        f.write(tokenize.untokenize(out_tokens))

files = [
    r"agent\agent_loop.py",
    r"config\settings.py",
    r"device\adb_controller.py",
    r"executor\skill_executor.py",
    r"main.py",
    r"planner\llm_planner.py",
    r"skills\__init__.py",
    r"skills\open_app.py",
    r"skills\press_key.py",
    r"skills\scroll.py",
    r"skills\tap.py",
    r"skills\type_text.py",
    r"tests\test_open_app_robustness.py",
    r"ui\dump_ui.py",
    r"ui\ui_parser.py"
]

base = r"d:\projects\mobile_agent"
for f in files:
    path = os.path.join(base, f)
    print(f"Processing {path}")
    remove_comments_from_file(path)
