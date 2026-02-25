import os
import sys
try:
    import Xlib
    import Xlib.display
    from Xlib import X
except ImportError:
    print("[ERROR] python-xlib is not installed in this environment.")
    sys.exit(1)

def diag():
    print("--- X11 Diagnostic ---")
    print(f"DISPLAY env: {os.environ.get('DISPLAY', 'NOT SET')}")
    
    try:
        display = Xlib.display.Display()
        print("Xlib Connection: SUCCESS")
    except Exception as e:
        print(f"Xlib Connection: FAILED ({e})")
        return

    screen = display.screen()
    root = screen.root
    
    # Check Active Window property
    NET_ACTIVE_WINDOW = display.intern_atom("_NET_ACTIVE_WINDOW")
    prop = root.get_full_property(NET_ACTIVE_WINDOW, X.AnyPropertyType)
    
    if not prop:
        print("[!] _NET_ACTIVE_WINDOW property NOT FOUND on root window.")
        print("    This usually means the Window Manager (Openbox/LXDE) isn't supporting EWMH.")
    else:
        window_id = prop.value[0]
        print(f"Active Window ID: {window_id}")
        
        if window_id == 0:
            print("[!] Active Window ID is 0 (No window focused).")
        else:
            try:
                window = display.create_resource_object("window", window_id)
                wm_class = window.get_wm_class()
                wm_name = window.get_wm_name()
                print(f"Window Class: {wm_class}")
                print(f"Window Name: {wm_name}")
                
                if not wm_class:
                    print("[!] Window has NO CLASS. Trying parent...")
                    parent = window.query_tree().parent
                    if parent:
                        print(f"Parent ID: {parent.id}")
                        print(f"Parent Class: {parent.get_wm_class()}")
            except Exception as e:
                print(f"[!] Error inspecting window: {e}")

    print("----------------------")

if __name__ == "__main__":
    diag()
