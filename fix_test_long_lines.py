import os

def fix_test(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    content = content.replace(
        'title="Test Job", source="Test", status=PrintStatus.DELETED, deleted_at=datetime.now(timezone.utc)',
        'title="Test Job",\n        source="Test",\n        status=PrintStatus.DELETED,\n        deleted_at=datetime.now(timezone.utc),'
    )
    content = content.replace(
        'title="Test Job", source="Test", status=PrintStatus.PRINTED, deleted_at=datetime.now(timezone.utc)',
        'title="Test Job",\n        source="Test",\n        status=PrintStatus.PRINTED,\n        deleted_at=datetime.now(timezone.utc),'
    )
    content = content.replace(
        'title="Skipped Job", source="Test", status=PrintStatus.SKIPPED, deleted_at=datetime.now(timezone.utc)',
        'title="Skipped Job",\n        source="Test",\n        status=PrintStatus.SKIPPED,\n        deleted_at=datetime.now(timezone.utc),'
    )
    content = content.replace(
        'title="Printed Job", source="Test", status=PrintStatus.PRINTED, deleted_at=datetime.now(timezone.utc)',
        'title="Printed Job",\n        source="Test",\n        status=PrintStatus.PRINTED,\n        deleted_at=datetime.now(timezone.utc),'
    )

    with open(filepath, 'w') as f:
        f.write(content)

fix_test("tests/unit/test_main.py")
