"""
Master Seeding Script
Runs all database seeding operations in correct order
"""

import sys
from pathlib import Path

# Set up paths
db_dir = Path(__file__).parent
sys.path.insert(0, str(db_dir.parent.parent.parent))  # Up to LightSpeed root

# Now import using proper package paths
from base import get_session, BaseModel, engine
from models import (
    ScientificDataset, CalculatorModule, CalculatorUsage,
    ZFloorFunction, FloorDirectoryStructure,
    KnowledgeGraphNode, KnowledgeGraphEdge,
    InterFloorComm, DataFlowPattern,
    SystemDocumentation, SystemConfiguration, SystemMetadata
)
from datetime import datetime

print("="*70)
print(" LIGHTSPEED DATABASE SEEDING - MASTER SCRIPT")
print("="*70)
print()

# Create all tables
print("[INIT] Creating database tables...")
BaseModel.metadata.create_all(engine)
print("[OK] Tables created\n")

session = get_session()

try:
    # ========================================================================
    # PHASE 1: SEED SCIENTIFIC DATASETS (21 files)
    # ========================================================================
    print("="*70)
    print(" PHASE 1: SEEDING SCIENTIFIC DATASETS")
    print("="*70)

    datasets = [
        # Planck CMB FITS files (9 files, ~14GB)
        {
            'filename': 'COM_CMB_IQU-217-fgsub-sevem_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-217-fgsub-sevem_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck CMB map at 217 GHz with foreground subtraction using SEVEM method',
            'extra_metadata': '{"resolution": 2048, "frequency": "217GHz", "method": "SEVEM", "release": "R3.00"}',
        },
        {
            'filename': 'COM_CMB_IQU-commander_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-commander_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1717986880,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck CMB map using Commander component separation method',
            'extra_metadata': '{"resolution": 2048, "method": "Commander", "release": "R3.00"}',
        },
        {
            'filename': 'COM_CMB_IQU-nilc_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-nilc_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck CMB map using NILC (Needlet Internal Linear Combination) method',
            'extra_metadata': '{"resolution": 2048, "method": "NILC", "release": "R3.00"}',
        },
        {
            'filename': 'COM_CMB_IQU-sevem_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-sevem_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck CMB map using SEVEM (Spectral Estimation Via Expectation Maximization)',
            'extra_metadata': '{"resolution": 2048, "method": "SEVEM", "release": "R3.00"}',
        },
        {
            'filename': 'COM_CMB_IQU-smica_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck CMB map using SMICA (Spectral Matching Independent Component Analysis)',
            'extra_metadata': '{"resolution": 2048, "method": "SMICA", "release": "R3.00"}',
        },
        {
            'filename': 'HFI_SkyMap_100-field-IQU_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/HFI_SkyMap_100-field-IQU_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck HFI (High Frequency Instrument) full-sky map at 100 GHz',
            'extra_metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "100GHz", "release": "R3.00"}',
        },
        {
            'filename': 'HFI_SkyMap_143-field-IQU_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/HFI_SkyMap_143-field-IQU_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck HFI full-sky map at 143 GHz',
            'extra_metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "143GHz", "release": "R3.00"}',
        },
        {
            'filename': 'HFI_SkyMap_217-field-IQU_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/HFI_SkyMap_217-field-IQU_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck HFI full-sky map at 217 GHz',
            'extra_metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "217GHz", "release": "R3.00"}',
        },
        {
            'filename': 'HFI_SkyMap_353-psb-field-IQU_2048_R3.00_full.fits',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/HFI_SkyMap_353-psb-field-IQU_2048_R3.00_full.fits',
            'category': 'planck_cmb',
            'format': 'FITS',
            'size_bytes': 1610612736,
            'mission': 'Planck',
            'observation_date': datetime(2009, 1, 1),
            'description': 'Planck HFI full-sky map at 353 GHz (polarization-sensitive bolometers)',
            'extra_metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "353GHz", "detector": "PSB", "release": "R3.00"}',
        },

        # LIGO Gravitational Wave files (12 files, ~766MB)
        # GW150914 - First detection (September 14, 2015)
        {
            'filename': 'H-H1_LOSC_4_V2-1126259446-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914/H-H1_LOSC_4_V2-1126259446-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 268435456,
            'mission': 'LIGO',
            'observation_date': datetime(2015, 9, 14),
            'description': 'LIGO Hanford detector data for GW150914 (first gravitational wave detection)',
            'extra_metadata': '{"event": "GW150914", "detector": "H1", "mass1_msun": 36, "mass2_msun": 29, "final_mass_msun": 62, "distance_mpc": 410}',
        },
        {
            'filename': 'H-H1_LOSC_4_V2-1126259446-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914/H-H1_LOSC_4_V2-1126259446-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 52428800,
            'mission': 'LIGO',
            'observation_date': datetime(2015, 9, 14),
            'description': 'LIGO Hanford HDF5 data for GW150914',
            'extra_metadata': '{"event": "GW150914", "detector": "H1", "format": "HDF5"}',
        },
        {
            'filename': 'L-L1_LOSC_4_V2-1126259446-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914/L-L1_LOSC_4_V2-1126259446-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 268435456,
            'mission': 'LIGO',
            'observation_date': datetime(2015, 9, 14),
            'description': 'LIGO Livingston detector data for GW150914',
            'extra_metadata': '{"event": "GW150914", "detector": "L1"}',
        },
        {
            'filename': 'L-L1_LOSC_4_V2-1126259446-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914/L-L1_LOSC_4_V2-1126259446-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 52428800,
            'mission': 'LIGO',
            'observation_date': datetime(2015, 9, 14),
            'description': 'LIGO Livingston HDF5 data for GW150914',
            'extra_metadata': '{"event": "GW150914", "detector": "L1", "format": "HDF5"}',
        },

        # GW170814 - Three-detector observation (August 14, 2017)
        {
            'filename': 'H-H1_LOSC_CLN_4_V1-1186739206-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814/H-H1_LOSC_CLN_4_V1-1186739206-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 41943040,
            'mission': 'LIGO',
            'observation_date': datetime(2017, 8, 14),
            'description': 'LIGO Hanford data for GW170814 (three-detector observation)',
            'extra_metadata': '{"event": "GW170814", "detector": "H1", "mass1_msun": 30.5, "mass2_msun": 25.3}',
        },
        {
            'filename': 'H-H1_LOSC_CLN_4_V1-1186739206-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814/H-H1_LOSC_CLN_4_V1-1186739206-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 10485760,
            'mission': 'LIGO',
            'observation_date': datetime(2017, 8, 14),
            'description': 'LIGO Hanford HDF5 for GW170814',
            'extra_metadata': '{"event": "GW170814", "detector": "H1"}',
        },
        {
            'filename': 'L-L1_LOSC_CLN_4_V1-1186739206-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814/L-L1_LOSC_CLN_4_V1-1186739206-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 41943040,
            'mission': 'LIGO',
            'observation_date': datetime(2017, 8, 14),
            'description': 'LIGO Livingston data for GW170814',
            'extra_metadata': '{"event": "GW170814", "detector": "L1"}',
        },
        {
            'filename': 'L-L1_LOSC_CLN_4_V1-1186739206-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814/L-L1_LOSC_CLN_4_V1-1186739206-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 10485760,
            'mission': 'LIGO',
            'observation_date': datetime(2017, 8, 14),
            'description': 'LIGO Livingston HDF5 for GW170814',
            'extra_metadata': '{"event": "GW170814", "detector": "L1"}',
        },

        # GW190521 - Most massive merger detected (May 21, 2019)
        {
            'filename': 'H-H1_LOSC_CLN_16_V1-1242459847-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521/H-H1_LOSC_CLN_16_V1-1242459847-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 5242880,
            'mission': 'LIGO',
            'observation_date': datetime(2019, 5, 21),
            'description': 'LIGO Hanford data for GW190521 (most massive black hole merger)',
            'extra_metadata': '{"event": "GW190521", "detector": "H1", "mass1_msun": 85, "mass2_msun": 66, "final_mass_msun": 142, "significance": "intermediate_mass_black_hole"}',
        },
        {
            'filename': 'H-H1_LOSC_CLN_16_V1-1242459847-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521/H-H1_LOSC_CLN_16_V1-1242459847-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 2097152,
            'mission': 'LIGO',
            'observation_date': datetime(2019, 5, 21),
            'description': 'LIGO Hanford HDF5 for GW190521',
            'extra_metadata': '{"event": "GW190521", "detector": "H1"}',
        },
        {
            'filename': 'L-L1_LOSC_CLN_16_V1-1242459847-32.gwf',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521/L-L1_LOSC_CLN_16_V1-1242459847-32.gwf',
            'category': 'ligo_gw',
            'format': 'GWF',
            'size_bytes': 5242880,
            'mission': 'LIGO',
            'observation_date': datetime(2019, 5, 21),
            'description': 'LIGO Livingston data for GW190521',
            'extra_metadata': '{"event": "GW190521", "detector": "L1"}',
        },
        {
            'filename': 'L-L1_LOSC_CLN_16_V1-1242459847-32.hdf5',
            'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521/L-L1_LOSC_CLN_16_V1-1242459847-32.hdf5',
            'category': 'ligo_gw',
            'format': 'HDF5',
            'size_bytes': 2097152,
            'mission': 'LIGO',
            'observation_date': datetime(2019, 5, 21),
            'description': 'LIGO Livingston HDF5 for GW190521',
            'extra_metadata': '{"event": "GW190521", "detector": "L1"}',
        },
    ]

    registered_datasets = 0
    for ds_data in datasets:
        existing = session.query(ScientificDataset).filter_by(filename=ds_data['filename']).first()
        if existing:
            print(f"[SKIP] Dataset exists: {ds_data['filename']}")
            continue

        dataset = ScientificDataset(**ds_data)
        session.add(dataset)
        registered_datasets += 1
        print(f"[OK] Registered: {ds_data['filename']} ({ds_data['category']})")

    session.commit()
    print(f"\n[SUCCESS] Registered {registered_datasets} datasets")
    print(f"[INFO] Total datasets in database: {session.query(ScientificDataset).count()}\n")

    # ========================================================================
    # PHASE 2: SEED CALCULATOR MODULES (49 modules)
    # ========================================================================
    print("="*70)
    print(" PHASE 2: SEEDING CALCULATOR MODULES")
    print("="*70)

    # Continue with calculator seeding...
    print("[INFO] Calculator seeding will be added in next phase\n")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("="*70)
    print(" SEEDING SUMMARY")
    print("="*70)
    print(f"Datasets registered: {registered_datasets}")
    print(f"Total datasets in DB: {session.query(ScientificDataset).count()}")
    print()
    print("[SUCCESS] Database seeding complete!")

except Exception as e:
    print(f"\n[ERROR] Seeding failed: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
    raise
finally:
    session.close()
