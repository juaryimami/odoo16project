import logging

print("Starting Menu Hierarchy Test...")

# Find the employee workspace menu
workspace_menu = env.ref('orbit_hr_workspace.menu_my_workspace', raise_if_not_found=False)
if not workspace_menu:
    print("FAILED: orbit_hr_workspace.menu_my_workspace not found!")
else:
    print(f"Found Workspace Menu: {workspace_menu.name} (ID: {workspace_menu.id})")

# Find the My Agreements menu
agreements_menu = env.ref('hr_policy_attestation.menu_my_agreements', raise_if_not_found=False)
if not agreements_menu:
    print("FAILED: hr_policy_attestation.menu_my_agreements not found!")
else:
    print(f"Found Agreements Menu: {agreements_menu.name} (ID: {agreements_menu.id})")
    
    if agreements_menu.parent_id.id == workspace_menu.id:
        print("SUCCESS: My Agreements is correctly placed under My Workspace!")
    else:
        print(f"FAILED: My Agreements is under {agreements_menu.parent_id.name} instead of My Workspace!")

print("Test Completed!")
