extends RefCounted

# Albedo detail cropped from Kaleb's supplied 18595.png, not a flat 3D substitute.
# Source SHA-256: bc95d8be5769951c7b75073952662d17d3a40e80017a14fdee2a6fe6ec8a79fc
# Crop: [416,780,530,895], resampled to 48x96 and quantized to 24 colors.
# Embedded bytes keep the authored texture in APK exports without broadening file filters.
const PNG_SHA256 := "f85c0beb09a5110da4281e765abf659403e9234d7307898416a8363f2989c437"
const PNG_BASE64 := """
iVBORw0KGgoAAAANSUhEUgAAADAAAABgCAMAAABsUgFCAAAASFBMVEXdh0nYgEPY
fkLWfULWe0HTekDOczvKbjbFazXCZzK+Yy67Xyy2Xyy0WyqyVyesViaoUSKlTR+c
SB6TQhqMPReCOhl9Nhd1MRXZndh3AAAE0klEQVR42p3Y25qjIAwAYFDOghxa7fu/
6SYcFKrO7G6nc+f/JUCIUBK8d25Rgs+ETJISQiehzbL6+BJiWdwaQkyv9+v93nb4
fIhHYAugAgErICUuH4FDAA9z+J8aiBSBr+D13kB8TjBDhA54n0IF8Pwd4BMA2oOV
qFvgnoAhuoL0CEg/BvUDsA2QA4QkiPkCWwa2TSvNz9MDzBWEXwADoAFEQm+Ba4DR
MogaIQYyjeDdIqx9BNpSiivhD8CNoKYU7b8CQwQAu17HcAecj5LIW+CtrevQjUG7
EHkD8QrWWt4DoETVCFit7xHABmJfIBCqM/ABi68HMBMZDClFTziM/RaYCnLp1XVw
sAyigSMlKL59BLSBNdlfAa2AFWC+QM1oBDCzEIBJBJpIBMsN0NablhJmxIQCoIhU
ME0twlb3z6cDmA+dJsYlgCiuYDtBmVZaInBMCYBC0FLaBxBKLY2AFuAq2I6UnDYN
TPhFoO/Bp0bQAGQFlLYI8wj2/weuA/jhBUhWwdpAfv4GsN+BCk5JAWA+QZD8CdgT
TDP8MVGB1s9gzWCaAcwVKK5GsA9A/w+YDoC1pC/gcwxaBg8pMQAMvo9g74EuYGaP
4NMB4RHwDkDXMEL/AEIFsHv+BsgGYNXYfIDHlIzw8QsYFxaMsDylFLUqoEyrhHWw
EKeCVAGK/RG4DrxO0FIyN0CrR7B+AVyH9V+BVxrbPe64K3BpqWA+VtqX7dCB7QHw
AoJSfYQNwHYAm6DPYLkCaIMuwLb3w7ZfAM/1fYCIwJ6gi6AzkAOAdxxOUgaxgX2I
IPl0BfBOrm/Rb+AOwEpKcL46wWXQJo5AHcD9ClgFAWYaxlDBu4C9AZ0Bo7kJ8Aqg
Ix4R3rinLwD6TF0HBK9VDeAaoTSmAuBA9vKwbgB8A1sHVMTWx0YQtLF9hAGcvfIE
sQdbBuXo4JYKviIkBNY2sHdAYvuG92h+PvdWOJC9Xsbk0rgFfs2tbwS2B3mSBoAb
YgBpxeft0WUK2BswFxD9ALatnWYagJXDD4eVhjNiSj4sNaW80Pg8VtMFzA3Y4FqE
OuZhDAVMM88pAYgmrDitsOEAlIzqGAwAuGflCOyI4FW+TVmfI9QhnMAu+NLqgZMr
3kQK2MthpgGlvDbfAHZ68Ln4EoJXfh6GgmNQGirTdAC2dJJiydcpX95wPbAAYAtA
bXDWQIwcQFjdWsBWDpXwKRFWeEh2ABofFdgvV19APYWWMVjYYFwYCZv0BHDORXaA
NAInONbGzFkuDUhpIQLqI/p6Wnp1EbxVixOz7gCc4OAU+iNQcMITIo8BI6xwicOb
VgoVpG7QFQh9AGF85HO+LVawjQAa1gAkAAo3Jqyoet04wEZCATMHICpY4LqBt3WY
oQy2C1jkTKE2BC/lvcB1QywGKzXGA+wlpQuAs/oSHUzSCfYT1AhGzgSnSRRg4TKg
CkgZvL5TMoIRpQ/g8qz2IH4DCbc2zCkDvcLVWJvyAn0AgkPtHADvZNjG1gO0lLYB
YLsswJMZQD7IJNzSqQ36BALmMb+rZy5NvulCa8UICPZ0jSAoz9u6AI1XLIOdu4DX
PTAVLHgB0vmHAWixuVhT+aVl68CcASuA34JPBhEBHvk4rLfgdBbSRljGHwG0pgxg
D9FJSIc3XW3uwR+N4tzDRcWWfwAAAABJRU5ErkJggg==
"""

static func create_texture() -> ImageTexture:
	var encoded := PNG_BASE64.replace("\n", "").replace("\r", "")
	var bytes := Marshalls.base64_to_raw(encoded)
	var hash := HashingContext.new()
	assert(hash.start(HashingContext.HASH_SHA256) == OK)
	assert(hash.update(bytes) == OK)
	assert(hash.finish().hex_encode() == PNG_SHA256, "T03 authored wood albedo hash mismatch")
	var image := Image.new()
	assert(image.load_png_from_buffer(bytes) == OK, "T03 authored wood albedo decode failed")
	assert(image.get_size() == Vector2i(48,96), "T03 authored wood albedo dimensions changed")
	image.convert(Image.FORMAT_RGBA8)
	assert(image.generate_mipmaps() == OK)
	return ImageTexture.create_from_image(image)
