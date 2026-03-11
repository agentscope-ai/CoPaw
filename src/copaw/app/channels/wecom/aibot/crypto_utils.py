"""
加解密工具模块

对标 Node.js SDK src/crypto.ts
提供文件加解密相关的功能函数，使用 AES-256-CBC 解密。
"""

import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def decrypt_file(encrypted_data: bytes, aes_key: str) -> bytes:
    """
    使用 AES-256-CBC 解密文件

    :param encrypted_data: 加密的文件数据
    :param aes_key: Base64 编码的 AES-256 密钥
    :return: 解密后的文件数据
    :raises ValueError: 参数无效时
    :raises RuntimeError: 解密失败时
    """
    if not encrypted_data:
        raise ValueError("decrypt_file: encrypted_data is empty or not provided")

    if not aes_key or not isinstance(aes_key, str):
        raise ValueError("decrypt_file: aes_key must be a non-empty string")

    # 将 Base64 编码的 aesKey 解码为 bytes
    # Node.js 的 Buffer.from(str, 'base64') 会自动容错处理缺少的 '=' padding，
    # 但 Python 的 base64.b64decode 严格要求长度是 4 的倍数，需要手动补齐。
    padded_aes_key = aes_key + '=' * (4 - len(aes_key) % 4) if len(aes_key) % 4 != 0 else aes_key
    key = base64.b64decode(padded_aes_key)

    # IV 取 aesKey 解码后的前 16 字节
    iv = key[:16]

    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        # 确保加密数据长度是 AES block size (16字节) 的倍数
        # Node.js 的 setAutoPadding(false) 不会对不对齐的数据报错，
        # 但 Python 的 cryptography 库会抛出 "Incorrect padding"。
        # 这里手动补零对齐，后续通过 PKCS#7 去除 padding 来获得正确数据。
        block_size = 16
        remainder = len(encrypted_data) % block_size
        if remainder != 0:
            encrypted_data = encrypted_data + b'\x00' * (block_size - remainder)

        # 解密（不自动处理 padding）
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()

        # 手动去除 PKCS#7 填充（支持 32 字节 block）
        if len(decrypted) == 0:
            raise ValueError("Decrypted data is empty")

        pad_len = decrypted[-1]
        if pad_len < 1 or pad_len > 32 or pad_len > len(decrypted):
            raise ValueError(f"Invalid PKCS#7 padding value: {pad_len}")

        # 验证所有 padding 字节是否一致
        for i in range(len(decrypted) - pad_len, len(decrypted)):
            if decrypted[i] != pad_len:
                raise ValueError("Invalid PKCS#7 padding: padding bytes mismatch")

        return decrypted[: len(decrypted) - pad_len]

    except Exception as e:
        raise RuntimeError(
            f"decrypt_file: Decryption failed - {e}. "
            "This may indicate corrupted data or an incorrect aesKey."
        ) from e
