import cv2
from tqdm import tqdm

from od_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

_NAME = "image_integrity"

@check(_NAME)
def validate_image_integrity(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    bad_images: list[str] = []
    total_images = 0

    for split in snap.splits:
        images = snap.images_per_split.get(split, ())
        for img_path in tqdm(images, desc=f"校验 {split} 图片", unit="img", leave=False):
            total_images += 1
            img = cv2.imread(str(img_path))
            if img is None:
                bad_images.append(str(img_path))

    if bad_images:
        return CheckResult(_NAME, CheckSeverity.ERROR,
                           f"{len(bad_images)}/{total_images} 张图片损坏或无法解码",
                           {"bad_images_preview": bad_images[:20]})
    return CheckResult(_NAME, CheckSeverity.PASS, f"全部 {total_images} 张图片均可正常解码")
