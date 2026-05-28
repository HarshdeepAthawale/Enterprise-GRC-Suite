import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.framework import FrameworkStandard, ControlCatalog, FrameworkControl

LOCAL_CSF_PATH = os.path.join(os.path.dirname(__file__), "nist_csf_2_0.json")


async def import_nist_csf(db: AsyncSession, force: bool = False):
    result = await db.execute(
        select(FrameworkStandard).where(
            FrameworkStandard.name == "NIST Cybersecurity Framework",
            FrameworkStandard.version == "2.0",
        )
    )
    existing = result.scalar_one_or_none()
    if existing and not force:
        print("NIST CSF 2.0 already imported. Use force=True to re-import.")
        return existing

    with open(LOCAL_CSF_PATH) as f:
        data = json.load(f)

    standard = FrameworkStandard(
        name="NIST Cybersecurity Framework",
        version="2.0",
        source_url=LOCAL_CSF_PATH,
        raw_import=data,
    )
    db.add(standard)
    await db.flush()

    for func in data.get("functions", []):
        func_cat = ControlCatalog(
            standard_id=standard.id,
            catalog_ref=func["id"],
            title=func["name"],
            description=func.get("description", ""),
            sort_order=int(func.get("sort_number", 0)) if func.get("sort_number") else 0,
        )
        db.add(func_cat)
        await db.flush()

        for cat in func.get("categories", []):
            cat_cat = ControlCatalog(
                standard_id=standard.id,
                catalog_ref=cat["id"],
                title=cat["name"],
                parent_id=func_cat.id,
                description=cat.get("description", ""),
                sort_order=int(cat.get("sort_number", 0)) if cat.get("sort_number") else 0,
            )
            db.add(cat_cat)
            await db.flush()

            for subcat in cat.get("subcategories", []):
                control = FrameworkControl(
                    catalog_id=cat_cat.id,
                    control_ref=subcat["id"],
                    name=subcat["name"],
                    description=subcat.get("description", ""),
                    implementation_examples=subcat.get("implementation_examples", []),
                )
                db.add(control)

    await db.commit()
    print(f"Imported NIST CSF 2.0: {len(data.get('functions', []))} functions")
    return standard
