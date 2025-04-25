import os.path
import numpy as np
from scipy.io import wavfile


class PhaseCoding:
    def __init__(self):
        self.rate = None
        self.data = None

    def convert_into_byte_array(self, audio_file):
        """Convert an audio into a byte array"""
        try:
            # Read the sample rate and data of the wav file
            self.rate, self.data = wavfile.read(audio_file)
        except wavfile.WavFileWarning:
            pass
        # Make data a copy of itself so that we can manipulate it without interfering the original audio
        self.data = self.data.copy()

    def encode(self, audio_address, secret_text):
        """Embed a secret text into an audio file"""

        # Convert the audio into a byte array
        self.convert_into_byte_array(audio_address)

        # Pad the secret text with "#" if its length is smaller than 100
        secret_text = secret_text.ljust(100, '#')

        # STEP 1: DIVIDE THE AUDIO INTO SMALLER BLOCKS

        # Calculate the number of secret text bits
        number_of_secret_text_bits = len(secret_text) * 8

        # Calculate the length of a single block
        block_length = int(4 * 2 ** np.ceil(np.log2(number_of_secret_text_bits)))

        # Calculate the number of blocks to be created
        block_number = int(np.ceil(self.data.shape[0] / block_length))

        # Check the number of dimension of the audio file

        # If the audio file is one-dimensional
        if len(self.data.shape) == 1:
            # Resize the data array to have size equals to the number of blocks
            self.data.resize(block_number * block_length, refcheck=False)

            # Increase the dimension of the audio by one, make it a two-dimensional audio
            self.data = self.data[np.newaxis]

        # Otherwise, if the audio file is multi-dimensional
        else:
            # Resize the data array so that:
            # - The number of columns is kept unchanged
            # - The number of rows equals to the number of blocks
            self.data.resize((block_number * block_length, self.data.shape[1]), refcheck=False)

            # Transpose the data array
            self.data = self.data.T

        # Split the first channel of the audio into blocks
        blocks = self.data[0].reshape((block_number, block_length))

        # STEP 2: APPLY DFT (DISCRETE FOURIER TRANSFORM) TO EACH BLOCK TO CREATE A MATRIX OF THE PHASES

        # Apply DFT using FFT
        blocks = np.fft.fft(blocks)

        # Calculate magnitude
        magnitudes = np.abs(blocks)

        # Create phase matrix
        phases = np.angle(blocks)

        # Get phase difference
        phase_differences = np.diff(phases, axis=0)

        # Create a list to store lists of bits of the characters in the secret text
        secret_text_bits = []

        # Store bits of each character into the list created
        for char in secret_text:
            # Convert the character to ASCII Value
            char_ascii = ord(char)

            # Convert the character in ASCII to binary value
            binary_char_ascii = bin(char_ascii).lstrip('0b')

            # Left padding the binary value of the character with 0s to make a complete byte
            binary_char_ascii_in_byte = binary_char_ascii.rjust(8, '0')

            # Create a list to store bits of this character
            bits = []

            # Store bits of this character into the list created
            for bit in binary_char_ascii_in_byte:
                bits.append(int(bit))

            # Store the list of bits of this character to the array of bits of the secret text
            secret_text_bits.append(bits)

        # Get the secret text in binary (an array of bits) form by flatten the
        secret_text_in_binary = np.ravel(secret_text_bits)

        # STEP 3: CONVERT THE SECRET TEXT INTO PHASE MODIFICATIONS

        # First, create a copy of the secret text in binary
        phase_modification = secret_text_in_binary.copy()

        # Modify the elements of the phase modification list:
        # - If a bit is equal to 0, then the phase modification in that position will be converted to +pi/2
        # - Otherwise, if a bit is equal to 1, then the phase modification in that position will be converted to -pi/2
        phase_modification[phase_modification == 0] = -1
        phase_modification = (-np.pi / 2) * phase_modification

        # Get middle location of a block:
        block_mid = block_length // 2  # "//" is the floor division

        # INSERT THE PHASE CONVERSIONS IN THE PHASE VECTOR OF THE FIRST SEGMENT
        phases[0, block_mid - number_of_secret_text_bits: block_mid] = phase_modification
        phases[0, block_mid + 1: block_mid + 1 + number_of_secret_text_bits] = -phase_modification[::-1]

        # STEP 4: CREATE A NEW PHASE MATRIX USING THE NEW PHASE OF THE SEGMENTS AND THE ORIGINAL PHASE MATRIX
        for i in range(1, len(phases)):
            phases[i] = phases[i - 1] + phase_differences[i - 1]

        # STEP 6: RE-CONSTRUCT THE SOUND SIGNAL BY APPLYING INVERSE DFT (DISCRETE FOURIER TRANSFORM)

        # Construct new blocks using original magnitudes with modified phases
        blocks = (magnitudes * np.exp(1j * phases))

        # Applying inverse DFT using IFFT
        blocks = np.fft.ifft(blocks).real

        # Combining all blocks of the first channel of the audio again (format 16-bit integer PCM):
        self.data[0] = blocks.ravel().astype(np.int16)

        # Save the encoded audio file and return its address
        return self.save_encoded_audio(self.data.T, audio_address)

    def save_encoded_audio(self, encoded_audio, address):
        """Save a stego audio file to a location"""

        # Get the directory of the audio
        addr = os.path.dirname(address)

        # Get the file name of the audio
        ori_file_name = os.path.basename(address).rstrip('.wav')

        # Set the address for the encoded audio
        new_audio_file_address = addr + '/' + ori_file_name + '-stego-pc.wav'

        # Create and write a new audio file which is the encoded audio file with the name specified above
        wavfile.write(new_audio_file_address, self.rate, encoded_audio)

        # Return the encoded audio file location
        return new_audio_file_address

    def decode(self, audio_address):
        """Decode a stego audio file to get the secret message"""

        # Convert the audio into a byte array
        self.convert_into_byte_array(audio_address)

        # Set initial number of secret text bits equals to 800
        number_of_secret_text_bits = 800

        # Calculate the length of a single block
        block_length = int(4 * 2 ** np.ceil(np.log2(number_of_secret_text_bits)))

        # Get middle location of a block:
        block_mid = block_length // 2   # "//" is floor division

        # Check the number of dimension of the audio file

        # If the audio file is one-dimensional
        if len(self.data.shape) == 1:
            # Retrieve the first block that contains the secret text
            secret = self.data[:block_length]

        # Otherwise, if the audio file is multi-dimensional
        else:
            # Retrieve the first block in the first channel that contains the secret text
            secret = self.data[:block_length, 0]

        # Apply DFT using FFT to the block and retrieve the phases containing the secret data in the location that we hid
        secret_phases = np.angle(np.fft.fft(secret))[block_mid - number_of_secret_text_bits:block_mid]

        # Convert the phases modifications back to the secret text in binary form

        # Create an array to store the bits of the secret text
        secret_in_binary = np.array([]).astype(np.int)

        # Store bits of the secret text into the array created above
        for phase in secret_phases:
            # Check if the phase is < 0, which means the phase can only be approximately -pi/2 -> convert it to bit 1
            if phase < 0:
                secret_in_binary = np.append(secret_in_binary, 1)
            # Otherwise, if the phase is >= 0, which means the phase can only be approximately pi/2 -> convert it to bit 0
            else:
                secret_in_binary = np.append(secret_in_binary, 0)

        # Convert the secret text to a byte array
        secret_in_bytes = secret_in_binary.reshape((-1, 8))

        # Create a list to store ASCII values of characters in the secret text
        ascii_values = []

        # Iterate through all the bytes in the byte array
        for byte in secret_in_bytes:
            char_ascii = 0

            # Calculate the ASCII value from the byte
            for i in range(8):
                char_ascii += byte[i] * 2 ** (7-i)

            # Store the ASCII value in the list created above
            ascii_values.append(char_ascii)

        # Get the padded secret text from the ASCII values
        padded_secret_text = ""
        for ascii_value in ascii_values:
            padded_secret_text += chr(ascii_value)

        # Retrieve the original secret text by get rid of the '###' part
        original_secret_text = padded_secret_text.split('###')[0]
        return original_secret_text