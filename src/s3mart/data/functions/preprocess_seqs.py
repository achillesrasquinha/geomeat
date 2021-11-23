import os.path as osp

from s3mart.config  import PATH
from s3mart import settings, __name__ as NAME

from bpyutils.util.ml      import get_data_dir
from bpyutils.util.system  import (
    ShellEnvironment,
    make_temp_dir, copy
)
from bpyutils import log

from s3mart.data.util import build_mothur_script

logger = log.get_logger(name = NAME)

CACHE  = PATH["CACHE"]

def preprocess_seqs(data_dir = None, *args, **kwargs):
    data_dir = get_data_dir(NAME, data_dir)
    jobs     = kwargs.get("jobs", settings.get("jobs"))

    merged_fasta = osp.join(data_dir, "merged.fasta")
    merged_group = osp.join(data_dir, "merged.group")

    silva_seed = kwargs["silva_seed"]
    silva_gold = kwargs["silva_gold"]
    silva_seed_tax = kwargs["silva_seed_tax"]

    files = (merged_fasta, merged_group, silva_seed, silva_gold, silva_seed_tax)

    with make_temp_dir(root_dir = CACHE) as tmp_dir:
        copy(*files, dest = tmp_dir)

        silva_seed_splitext = osp.splitext(osp.basename(silva_seed))

        mothur_file = osp.join(tmp_dir, "script")
        build_mothur_script(
            template = "mothur/preprocess",
            output   = mothur_file,
            merged_fasta = osp.join(tmp_dir, osp.basename(merged_fasta)),
            merged_group = osp.join(tmp_dir, osp.basename(merged_group)),

            silva_seed       = osp.join(tmp_dir, osp.basename(silva_seed)),
            silva_seed_start = settings.get("silva_seed_pcr_start"),
            silva_seed_end   = settings.get("silva_seed_pcr_end"),

            silva_seed_pcr   = osp.join(tmp_dir, "%s.pcr%s" % (silva_seed_splitext[0], silva_seed_splitext[1])),
            
            silva_seed_tax   = osp.join(tmp_dir, osp.basename(silva_seed_tax)),
            silva_gold       = osp.join(tmp_dir, osp.basename(silva_gold)),

            maxhomop         = settings.get("maximum_homopolymers"),

            processors       = jobs
        )

        with ShellEnvironment(cwd = tmp_dir) as shell:
            code = shell("mothur %s" % mothur_file)

            if not code:
                pass
            else:
                logger.error("Error merging files.")