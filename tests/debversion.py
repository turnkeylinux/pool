import re

def deb_compare_versions(a, b):
    """Compare a with b according to Debian versioning criteria"""

    def normalize(v):
        return re.sub(r'(\D|\b)0+', r'\1', v).rstrip("-")
        
    return cmp(normalize(a), normalize(b))

def main():
    dcv = deb_compare_versions
    assert dcv('1', '2') < 0
    assert dcv('1.01', '1.1') == 0
    assert dcv('1.02', '1.1') > 0
    assert dcv('-1', '0-1') == 0
    assert dcv('1:1', '1.1') > 0
    assert dcv('1.1', '1-1') > 0
    assert dcv('1', '1-000') == 0

if __name__ == "__main__":
    main()

