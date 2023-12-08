from PIL import Image
import numpy as np
import base64
import json
import streamlit as st

# The encryption functions (as provided in your code)
def rotate180(n):
    bits = "{0:b}".format(n)
    return int(bits[::-1], 2)

def create_key(m, n, alpha):
    Kr = [np.random.randint(0, 2**alpha - 1) for _ in range(m)]
    Kc = [np.random.randint(0, 2**alpha - 1) for _ in range(n)]
    iter_max = 10  # You can adjust this value based on your requirement

    key_dict = {
        "Kr": Kr,
        "Kc": Kc,
        "iter_max": iter_max
    }

    return key_dict

def roll_row(matrix, key, encrypt_flag=True):
    direction_multiplier = 1 if encrypt_flag else -1

    for i in range(len(matrix)):
        modulus = np.sum(matrix[i, :, 0]) % 2
        matrix[i, :, 0] = np.roll(matrix[i, :, 0], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[i, :, 0], -direction_multiplier * key[i])
        modulus = np.sum(matrix[i, :, 1]) % 2
        matrix[i, :, 1] = np.roll(matrix[i, :, 1], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[i, :, 1], -direction_multiplier * key[i])
        modulus = np.sum(matrix[i, :, 2]) % 2
        matrix[i, :, 2] = np.roll(matrix[i, :, 2], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[i, :, 2], -direction_multiplier * key[i])

def roll_column(matrix, key, encrypt_flag=True):
    direction_multiplier = 1 if encrypt_flag else -1

    for i in range(len(matrix[0])):
        modulus = np.sum(matrix[:, i, 0]) % 2
        matrix[:, i, 0] = np.roll(matrix[:, i, 0], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[:, i, 0], -direction_multiplier * key[i])
        modulus = np.sum(matrix[:, i, 1]) % 2
        matrix[:, i, 1] = np.roll(matrix[:, i, 1], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[:, i, 1], -direction_multiplier * key[i])
        modulus = np.sum(matrix[:, i, 2]) % 2
        matrix[:, i, 2] = np.roll(matrix[:, i, 2], direction_multiplier * key[i]) if modulus == 0 else np.roll(matrix[:, i, 2], -direction_multiplier * key[i])

def xor_pixels(matrix, Kr, Kc):
    m, n, _ = matrix.shape

    for i in range(m):
        for j in range(n):
            xor_operand_1 = Kc[j] if i % 2 == 1 else rotate180(Kc[j])
            xor_operand_2 = Kr[i] if j % 2 == 0 else rotate180(Kr[i])

            matrix[i, j, 0] ^= xor_operand_1 ^ xor_operand_2
            matrix[i, j, 1] ^= xor_operand_1 ^ xor_operand_2
            matrix[i, j, 2] ^= xor_operand_1 ^ xor_operand_2

# Function to encrypt the image and save the key
def encrypt_image(input_image, alpha=8):
    matrix = np.array(input_image)

    m, n, _ = matrix.shape
    key = create_key(m, n, alpha)
    Kr, Kc = key["Kr"], key["Kc"]

    for _ in range(key["iter_max"]):
        roll_row(matrix, Kc)
        roll_column(matrix, Kc)
        xor_pixels(matrix, Kr, Kc)

    encrypted_image = Image.fromarray(matrix.astype(np.uint8))

    # Save the key as a downloadable link
    serialized_key = base64.b64encode(json.dumps(key).encode()).decode()
    with open("encryption_key.txt", "w") as key_file:
        key_file.write(serialized_key)

    return encrypted_image, serialized_key

# Function to decrypt the image using the provided key
def decrypt_image(encrypted_image, key):
    matrix = np.array(encrypted_image)
    Kr, Kc = key["Kr"], key["Kc"]

    # Reverse the encryption process
    for _ in range(key["iter_max"]):
        xor_pixels(matrix, Kr, Kc)
        roll_column(matrix, Kc, encrypt_flag=False)
        roll_row(matrix, Kc, encrypt_flag=False)

    decrypted_image = Image.fromarray(matrix.astype(np.uint8))
    return decrypted_image

# Streamlit app
def main():
    st.title("Image Encryption App")

    # Encryption page
    st.header("Encryption")
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        if st.button("Encrypt Image"):
            # try:
                # Perform encryption
                encrypted_image, serialized_key = encrypt_image(Image.open(uploaded_file))
                st.image(encrypted_image, caption="Encrypted Image", use_column_width=True)

                # Provide download link for the key
                st.markdown(
                    f"Download the encryption key: [encryption_key.txt](data:file/txt;base64,{serialized_key})",
                    unsafe_allow_html=True
                )

                # Provide download link for the encrypted image
                encrypted_image_filename = "encrypted_image.png"
                st.markdown(
                    f"Download the encrypted image: [encrypted_image.png](data:file/png;base64,{base64.b64encode(encrypted_image.tobytes()).decode()})",
                    unsafe_allow_html=True
                )

    # Decryption page
    st.header("Decryption")
    st.subheader("Decrypt Image using Key")

    # User input for encrypted image
    uploaded_encrypted_file = st.file_uploader("Choose the encrypted image file", type=["png"])
    if uploaded_encrypted_file is not None:
        st.image(uploaded_encrypted_file, caption="Uploaded Encrypted Image", use_column_width=True)

        # User input for the key file
        uploaded_key_file = st.file_uploader("Choose the key file (encryption_key.txt)", type=["txt"])
        if uploaded_key_file is not None:
            # Decrypt the image using the provided key
            try:
                key_content = uploaded_key_file.read()
                decoded_key = base64.b64decode(key_content).decode()
                key = json.loads(decoded_key)

                decrypted_image = decrypt_image(Image.open(uploaded_encrypted_file), key)
                st.image(decrypted_image, caption="Decrypted Image", use_column_width=True)

            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
