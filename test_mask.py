from mask import mask_pii

# Synthetic fixture only. No real bill data in this repo.
sample = """
MADHYA PRADESH SAMPLE DISCOM
Consumer Name: RAHUL TESTKUMAR SHARMA
Name: RAHUL TESTKUMAR SHARMA
Address: PLOT 12, TEST NAGAR, BHOPAL 462001
VILLAGE TESTPUR WARD 12 TEHSIL HUZUR
Consumer No: X1234567890
Meter No: Z1234567
PAN: ABCDE1234F
Mobile: 9876543210
Alt: +91 9876543210
Masked: ******4321
Email: test.user@example.com
Account: 123456789012
Old pin ref 462002
Bill Month: September-2026
Net Payable: 1234.00
"""
masked = mask_pii(sample)
for needle in ['ABCDE1234F', 'abcde1234f', 'X1234567890', 'Z1234567', 'test.user@example.com',
               '9876543210', '******4321', 'TEST NAGAR', 'VILLAGE TESTPUR', '462001',
               'RAHUL TESTKUMAR SHARMA', '123456789012']:
    assert needle not in masked, f"still present: {needle}"
for token in ['[PAN MASKED]', '[CONSUMER CODE MASKED]', '[METER NO MASKED]', '[EMAIL MASKED]',
              '[PHONE MASKED]', '[ADDRESS MASKED]', '[NAME MASKED]', '[ACCOUNT NO MASKED]', '[PIN MASKED]']:
    assert token in masked, f"missing token: {token}"
# Lowercase PAN must also mask
assert 'wxyzt9876k' not in mask_pii('pan wxyzt9876k here')
# Bill numbers and amounts must survive
assert '1234.00' in masked and 'September-2026' in masked
print("masking ok: synthetic PAN/consumer/meter/email/phone/address/name/account/pin all masked; amounts and dates survive")
