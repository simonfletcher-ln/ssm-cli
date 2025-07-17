from ssm_cli.config import config

def select(instances: list):
    try:
        import tkinter as tk
        import tkinter.ttk as ttk
    except ModuleNotFoundError:
        raise ModuleNotFoundError("tkinter missing, see README")
    
    response = None
    # handlers
    def close():
        nonlocal response
        response = instance_map[last_selected_item]
        window.destroy()

    def on_select(event):
        nonlocal last_selected_item
        last_selected_item = tree.selection()[0]
        if 'offline' in tree.item(last_selected_item, 'tags'):
            select_button.config(state=tk.DISABLED)
        else:
            select_button.config(state=tk.NORMAL)
    
    def on_enter(event):
        if select_button['state'] == tk.NORMAL:
            close()

    window = tk.Tk()
    window.geometry(config.gui.size)
    window.title(config.gui.title)

    # Create and populate tree
    cols = list(config.gui.tree_columns.keys())
    tree = ttk.Treeview(window, columns=cols, show='headings', selectmode='browse')
    for name, width in config.gui.tree_columns.items():
        tree.heading(name, text=name)
        tree.column(name, width=width)

    if config.gui.offline_background:
        tree.tag_configure('offline', background=config.gui.offline_background)

    instance_map = {}
    last_selected_item = None
    for i, instance in enumerate(instances):
        tags = []
        online = instance.ping == 'Online'
        if not online:
            tags.append('offline')
        id = tree.insert('', index=i, text="", values=[getattr(instance, x) for x in cols], tags=tags)
        instance_map[id] = instance
        if last_selected_item is None and online:
            last_selected_item = id
            tree.selection_set(id)
            tree.focus(id)

    # Create and configure scrollbar
    rightScrollbar = tk.Scrollbar(window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=rightScrollbar.set)

    # create buttons
    button_frame = tk.Frame(window)
    select_button = tk.Button(button_frame, text="Select", command=close)
    cancel_button = tk.Button(button_frame, text="Cancel", command=window.destroy)

    # bind to events
    tree.bind("<<TreeviewSelect>>", on_select)
    window.bind('<Escape>', lambda event: window.destroy())
    window.bind('<Return>', on_enter)

    # pack everything up, order matters
    rightScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=tk.YES)
    button_frame.pack(side=tk.BOTTOM)
    select_button.pack(side=tk.RIGHT, padx=5, pady=5)
    cancel_button.pack(side=tk.LEFT, padx=5, pady=5)

    window.after(100, lambda: tree.focus_set())
    window.mainloop()

    return response