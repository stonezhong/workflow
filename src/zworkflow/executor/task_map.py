import importlib

ACTIVITY_HANDLER_MAP = {
}

def generate_task_map(task_config_filename:dict):
    for task_key, v in task_config_filename.items():
        for task_version, full_method_name in v.items():
            module_name, method_name = full_method_name.split(":")
            print(f"Loading handler for {task_key}:{task_version}")
            mod = importlib.import_module(module_name)
            method = getattr(mod, method_name)

            if task_key not in ACTIVITY_HANDLER_MAP:
                ACTIVITY_HANDLER_MAP[task_key] = {}
            
            ACTIVITY_HANDLER_MAP[task_key][task_version] = method
    
