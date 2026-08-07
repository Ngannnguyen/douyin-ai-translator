import os
import sys

# Giới hạn các thư viện tính toán trước khi chúng được nạp. Điều này chỉ áp
# dụng cho ứng dụng, không thay đổi cấu hình Windows hoặc ứng dụng khác.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

if __name__ == "__main__":
    if "--self-test" in sys.argv or "--full-self-test" in sys.argv:
        from douyin_translator.self_test import run_self_test

        raise SystemExit(run_self_test(full="--full-self-test" in sys.argv))

    from douyin_translator.ui import TranslatorApp

    TranslatorApp().run()
