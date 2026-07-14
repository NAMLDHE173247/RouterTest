import sys
import importlib

def load_isolated_router(path: str):
    """
    Loads `rule_router.route_question` from the given path in isolation,
    preventing module conflicts between V0, V1, V2.
    """
    conflict_modules = ['rule_router', 'rules', 'keyword_matcher']
    
    # Save original modules
    original_modules = {}
    for mod in conflict_modules:
        if mod in sys.modules:
            original_modules[mod] = sys.modules.pop(mod)
            
    # Add path to sys.path
    sys.path.insert(0, path)
    
    try:
        # Import rule_router from the inserted path
        import rule_router
        # Get the reference to the function
        route_fn = rule_router.route_question
        return route_fn
    finally:
        # Remove path
        if sys.path[0] == path:
            sys.path.pop(0)
            
        # Remove newly loaded modules from cache
        for mod in conflict_modules:
            if mod in sys.modules:
                del sys.modules[mod]
                
        # Restore original modules
        for mod, original in original_modules.items():
            sys.modules[mod] = original
