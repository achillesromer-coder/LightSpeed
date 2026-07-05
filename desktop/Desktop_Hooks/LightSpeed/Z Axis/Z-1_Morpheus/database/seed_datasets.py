"""
Seed Scientific Datasets into Database
Registers all 21 scientific data files (Planck CMB, LIGO, databases, simulations)
"""

import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from local modules
from models import ScientificDataset
from base import get_session

# Dataset definitions
DATASETS = [
    # Planck CMB FITS files (9 files, ~14GB)
    {
        'filename': 'COM_CMB_IQU-217-fgsub-sevem_2048_R3.00_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-217-fgsub-sevem_2048_R3.00_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 1006632960,  # ~961MB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using SEVEM component separation method with 217 GHz foreground subtraction',
        'metadata': '{"resolution": 2048, "method": "SEVEM", "frequency": "217GHz", "release": "R3.00"}',
    },
    {
        'filename': 'COM_CMB_IQU-commander_2048_R3.00_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-commander_2048_R3.00_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 1717986880,  # ~1.6GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using Commander component separation method',
        'metadata': '{"resolution": 2048, "method": "Commander", "release": "R3.00"}',
    },
    {
        'filename': 'COM_CMB_IQU-nilc_2048_R3.00_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-nilc_2048_R3.00_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 1717986880,  # ~1.6GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using NILC (Needlet Internal Linear Combination) method',
        'metadata': '{"resolution": 2048, "method": "NILC", "release": "R3.00"}',
    },
    {
        'filename': 'COM_CMB_IQU-sevem_2048_R3.01_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-sevem_2048_R3.01_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 2040109056,  # ~1.9GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using SEVEM component separation method (updated release)',
        'metadata': '{"resolution": 2048, "method": "SEVEM", "release": "R3.01"}',
    },
    {
        'filename': 'COM_CMB_IQU-smica_2048_R3.00_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 2040109056,  # ~1.9GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using SMICA (Spectral Matching Independent Component Analysis) method',
        'metadata': '{"resolution": 2048, "method": "SMICA", "release": "R3.00"}',
    },
    {
        'filename': 'COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 403701760,  # ~385MB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck CMB map using SMICA method without Sunyaev-Zeldovich correction',
        'metadata': '{"resolution": 2048, "method": "SMICA-NoSZ", "release": "R3.00"}',
    },
    {
        'filename': 'HFI_SkyMap_100_2048_R2.02_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/HFI_SkyMap_100_2048_R2.02_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 2040109056,  # ~1.9GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck HFI full sky map at 100 GHz',
        'metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "100GHz", "release": "R2.02"}',
    },
    {
        'filename': 'NASA - IPAC; Planck_HFI_SkyMap_143_2048_R2.02_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/NASA - IPAC; Planck_HFI_SkyMap_143_2048_R2.02_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 2040109056,  # ~1.9GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck HFI full sky map at 143 GHz (NASA IPAC archive)',
        'metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "143GHz", "release": "R2.02", "source": "NASA-IPAC"}',
    },
    {
        'filename': 'NASA-IPAC; Planck HFI_SkyMap_100_2048_R2.02_full.fits',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/planck_cmb/NASA-IPAC; Planck HFI_SkyMap_100_2048_R2.02_full.fits',
        'category': 'planck_cmb',
        'format': 'FITS',
        'size_bytes': 2040109056,  # ~1.9GB
        'mission': 'Planck',
        'observation_date': '2009-2013',
        'description': 'Planck HFI full sky map at 100 GHz (NASA IPAC archive)',
        'metadata': '{"resolution": 2048, "instrument": "HFI", "frequency": "100GHz", "release": "R2.02", "source": "NASA-IPAC"}',
    },

    # LIGO Gravitational Wave files (12 files, ~766MB)
    # GW150914 - First gravitational wave detection
    {
        'filename': 'GW150914(GWF)H-H1_GWOSC_16KHZ_R1-1126259447-32.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914(GWF)H-H1_GWOSC_16KHZ_R1-1126259447-32.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2015-09-14',
        'description': 'GW150914 gravitational wave data - First direct detection (16kHz, Hanford H1)',
        'metadata': '{"event": "GW150914", "detector": "H1-Hanford", "sample_rate": "16kHz", "masses": "36+29 M☉", "distance": "410 Mpc"}',
    },
    {
        'filename': 'GW150914(GWF)H-H1_GWOSC_4KHZ_R1-1126257415-4096.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914(GWF)H-H1_GWOSC_4KHZ_R1-1126257415-4096.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 131072000,  # ~125MB
        'mission': 'LIGO',
        'observation_date': '2015-09-14',
        'description': 'GW150914 gravitational wave data - First direct detection (4kHz, Hanford H1)',
        'metadata': '{"event": "GW150914", "detector": "H1-Hanford", "sample_rate": "4kHz", "duration": "4096s"}',
    },
    {
        'filename': 'GW150914(HDF)H-H1_GWOSC_16KHZ_R1-1126259447-32.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914(HDF)H-H1_GWOSC_16KHZ_R1-1126259447-32.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2015-09-14',
        'description': 'GW150914 gravitational wave data in HDF5 format (16kHz, Hanford H1)',
        'metadata': '{"event": "GW150914", "detector": "H1-Hanford", "sample_rate": "16kHz", "format": "HDF5"}',
    },
    {
        'filename': 'GW150914(HDF)H-H1_GWOSC_4KHZ_R1-1126257415-4096.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW150914(HDF)H-H1_GWOSC_4KHZ_R1-1126257415-4096.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 131072000,  # ~125MB
        'mission': 'LIGO',
        'observation_date': '2015-09-14',
        'description': 'GW150914 gravitational wave data in HDF5 format (4kHz, Hanford H1)',
        'metadata': '{"event": "GW150914", "detector": "H1-Hanford", "sample_rate": "4kHz", "format": "HDF5"}',
    },

    # GW170814 - First three-detector observation
    {
        'filename': 'GW170814(GWF)- L-L1_GWOSC_4KHZ_R1-1186739814-4096.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814(GWF)- L-L1_GWOSC_4KHZ_R1-1186739814-4096.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 130023424,  # ~124MB
        'mission': 'LIGO',
        'observation_date': '2017-08-14',
        'description': 'GW170814 gravitational wave data - First three-detector observation (4kHz, Livingston L1)',
        'metadata': '{"event": "GW170814", "detector": "L1-Livingston", "sample_rate": "4kHz", "masses": "31+25 M☉"}',
    },
    {
        'filename': 'GW170814(GWF)L-L1_GWOSC_16KHZ_R1-1186741846-32.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814(GWF)L-L1_GWOSC_16KHZ_R1-1186741846-32.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2017-08-14',
        'description': 'GW170814 gravitational wave data (16kHz, Livingston L1)',
        'metadata': '{"event": "GW170814", "detector": "L1-Livingston", "sample_rate": "16kHz"}',
    },
    {
        'filename': 'GW170814(HDF)L-L1_GWOSC_16KHZ_R1-1186741846-32.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814(HDF)L-L1_GWOSC_16KHZ_R1-1186741846-32.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2017-08-14',
        'description': 'GW170814 gravitational wave data in HDF5 format (16kHz, Livingston L1)',
        'metadata': '{"event": "GW170814", "detector": "L1-Livingston", "sample_rate": "16kHz", "format": "HDF5"}',
    },
    {
        'filename': 'GW170814(HDF)L-L1_GWOSC_4KHZ_R1-1186739814-4096.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW170814(HDF)L-L1_GWOSC_4KHZ_R1-1186739814-4096.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 130023424,  # ~124MB
        'mission': 'LIGO',
        'observation_date': '2017-08-14',
        'description': 'GW170814 gravitational wave data in HDF5 format (4kHz, Livingston L1)',
        'metadata': '{"event": "GW170814", "detector": "L1-Livingston", "sample_rate": "4kHz", "format": "HDF5"}',
    },

    # GW190521 - Most massive black hole merger
    {
        'filename': 'GW190521(GWF)H-H1_GWOSC_16KHZ_R1-1242442952-32.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521(GWF)H-H1_GWOSC_16KHZ_R1-1242442952-32.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2019-05-21',
        'description': 'GW190521 gravitational wave data - Most massive black hole merger (16kHz, Hanford H1)',
        'metadata': '{"event": "GW190521", "detector": "H1-Hanford", "sample_rate": "16kHz", "masses": "85+66 M☉", "final_mass": "142 M☉"}',
    },
    {
        'filename': 'GW190521(GWF)H-H1_GWOSC_4KHZ_R1-1242440920-4096.gwf',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521(GWF)H-H1_GWOSC_4KHZ_R1-1242440920-4096.gwf',
        'category': 'ligo_gw',
        'format': 'GWF',
        'size_bytes': 130023424,  # ~124MB
        'mission': 'LIGO',
        'observation_date': '2019-05-21',
        'description': 'GW190521 gravitational wave data (4kHz, Hanford H1)',
        'metadata': '{"event": "GW190521", "detector": "H1-Hanford", "sample_rate": "4kHz"}',
    },
    {
        'filename': 'GW190521(HDF)H-H1_GWOSC_16KHZ_R1-1242442952-32.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521(HDF)H-H1_GWOSC_16KHZ_R1-1242442952-32.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 4088832,  # ~3.9MB
        'mission': 'LIGO',
        'observation_date': '2019-05-21',
        'description': 'GW190521 gravitational wave data in HDF5 format (16kHz, Hanford H1)',
        'metadata': '{"event": "GW190521", "detector": "H1-Hanford", "sample_rate": "16kHz", "format": "HDF5"}',
    },
    {
        'filename': 'GW190521(HDF)H-H1_GWOSC_4KHZ_R1-1242440920-4096.hdf5',
        'filepath': 'Z Axis/Z0_TheConstruct/data/datasets/ligo_gw/GW190521(HDF)H-H1_GWOSC_4KHZ_R1-1242440920-4096.hdf5',
        'category': 'ligo_gw',
        'format': 'HDF5',
        'size_bytes': 130023424,  # ~124MB
        'mission': 'LIGO',
        'observation_date': '2019-05-21',
        'description': 'GW190521 gravitational wave data in HDF5 format (4kHz, Hanford H1)',
        'metadata': '{"event": "GW190521", "detector": "H1-Hanford", "sample_rate": "4kHz", "format": "HDF5"}',
    },
]


def seed_datasets():
    """Seed all scientific datasets into database"""
    session = get_session()

    try:
        print("[SEED] Starting scientific dataset registration...")
        print(f"[SEED] Total datasets to register: {len(DATASETS)}")

        # Calculate totals
        planck_count = len([d for d in DATASETS if d['category'] == 'planck_cmb'])
        ligo_count = len([d for d in DATASETS if d['category'] == 'ligo_gw'])
        total_size = sum(d['size_bytes'] for d in DATASETS)

        print(f"[INFO] Planck CMB files: {planck_count}")
        print(f"[INFO] LIGO GW files: {ligo_count}")
        print(f"[INFO] Total size: {total_size / (1024**3):.2f} GB")
        print()

        registered = 0
        skipped = 0

        for dataset_data in DATASETS:
            # Check if already exists
            existing = session.query(ScientificDataset).filter_by(
                filename=dataset_data['filename']
            ).first()

            if existing:
                print(f"[SKIP] {dataset_data['filename']}")
                skipped += 1
                continue

            # Create new dataset
            dataset = ScientificDataset(**dataset_data)
            session.add(dataset)
            registered += 1

            size_mb = dataset_data['size_bytes'] / (1024**2)
            print(f"[OK] Registered: {dataset_data['filename']} ({size_mb:.1f}MB, {dataset_data['category']})")

        session.commit()

        print()
        print(f"[SUCCESS] Registered {registered} new datasets")
        print(f"[INFO] Skipped {skipped} existing datasets")
        print(f"[INFO] Total datasets in database: {session.query(ScientificDataset).count()}")

        # Show summary by category
        print("\n[SUMMARY] Datasets by category:")
        for category in ['planck_cmb', 'ligo_gw']:
            count = session.query(ScientificDataset).filter_by(category=category).count()
            total = session.query(ScientificDataset).filter_by(category=category)
            size_gb = sum(d.size_bytes for d in total) / (1024**3)
            print(f"  {category}: {count} files, {size_gb:.2f} GB")

    except Exception as e:
        print(f"[ERROR] Failed to seed datasets: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_datasets()
