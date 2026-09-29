"""Disabled legacy mock loader.

Historical synthetic fixtures are retained only in the forensic snapshot/test archive.
Production discovery must never seed business evidence from this module.
"""
class MockLoader:
    def __init__(self,*args,**kwargs):
        raise RuntimeError('MockLoader is disabled for forensic recovery. Use real collectors or explicit test fixtures.')
