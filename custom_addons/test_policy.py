import logging

_logger = logging.getLogger(__name__)

# Test HR Policy Management Module

print("Starting HR Policy Module Test...")

# 1. Create a dummy employee
employee = env['hr.employee'].create({
    'name': 'Test Policy Employee',
})
print(f"Created employee: {employee.name} (ID: {employee.id})")

# 2. Create a Policy Template
template = env['hr.policy.template'].create({
    'name': 'Test Security Policy',
    'content_type': 'text',
    'body_html': '<p>Be secure!</p>',
    'target_type': 'specific',
    'employee_ids': [(6, 0, [employee.id])]
})
print(f"Created Template: {template.name} (ID: {template.id})")

# 3. Publish Version 1.0 using the Wizard
wizard = env['hr.policy.publish.wizard'].create({
    'template_id': template.id,
    'version_num': 'v1.0',
    'is_major': True,
})
wizard.action_publish()
print("Published Version v1.0")

# 4. Validate Attestation Generation
attestations = env['hr.policy.attestation'].search([('employee_id', '=', employee.id), ('template_id', '=', template.id)])
print(f"Found {len(attestations)} attestations for employee.")
for att in attestations:
    print(f" - Attestation ID: {att.id}, Status: {att.status}, Version: {att.version_id.version_num}")
    
    # 5. Simulate signing the document
    att.with_context(allow_status_update=True).write({
        'status': 'agreed',
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 Scratchpad Test'
    })
    print(f" - Signed Document. New Status: {att.status}")

# 6. Publish Version 1.1 (Minor Update)
wizard2 = env['hr.policy.publish.wizard'].create({
    'template_id': template.id,
    'version_num': 'v1.1',
    'is_major': False,
})
wizard2.action_publish()
print("Published Version v1.1 (Minor)")

# 7. Check Attestation status for minor version (Should automatically be agreed)
attestations_v1_1 = env['hr.policy.attestation'].search([('employee_id', '=', employee.id), ('version_id.version_num', '=', 'v1.1')])
for att in attestations_v1_1:
    print(f" - New Attestation ID: {att.id}, Status: {att.status}, Version: {att.version_id.version_num}")
    assert att.status == 'agreed', "Minor version failed to inherit 'agreed' status!"

# 8. Publish Version 2.0 (Major Update)
wizard3 = env['hr.policy.publish.wizard'].create({
    'template_id': template.id,
    'version_num': 'v2.0',
    'is_major': True,
})
wizard3.action_publish()
print("Published Version v2.0 (Major)")

# 9. Check Attestation status for major version (Should be pending)
attestations_v2_0 = env['hr.policy.attestation'].search([('employee_id', '=', employee.id), ('version_id.version_num', '=', 'v2.0')])
for att in attestations_v2_0:
    print(f" - New Attestation ID: {att.id}, Status: {att.status}, Version: {att.version_id.version_num}")
    assert att.status == 'pending', "Major version failed to reset to 'pending' status!"

# Cleanup test data to keep db clean
template.unlink()
employee.unlink()
print("Cleaned up test data.")
print("Test completed successfully!")
env.cr.commit()
