"""OAEI knowledge graph track dataset class."""

import os
from collections import namedtuple

from forayer.datasets.base_dataset import RemoteDataset
from forayer.input_output.from_to_rdf import load_from_rdf
from forayer.knowledge_graph import ClusterHelper, ERTask
from rdflib import Graph
from tqdm import tqdm

URLWithFileName = namedtuple("URLWithFileName", ["url", "file_name"])
OAEITaskFiles = namedtuple(
    "OAEITaskFiles",
    [
        "kg1",
        "kg2",
        "ref",
    ],
)


class OAEIKGDataset(RemoteDataset):
    """The  OAEI (Ontology Alignment Evaluation Initiative) Knowledge Graph Track tasks contain graphs created from fandom wikis.

    Five integration tasks are available:
        - starwars-swg
        - starwars-swtor
        - marvelcinematicuniverse-marvel
        - memoryalpha-memorybeta
        - memoryalpha-stexpanded

    More information can be found at the `website <http://oaei.ontologymatching.org/2019/knowledgegraph/index.html>`_.
    """

    DS_NAME = "OAEI_KG_Track"

    _STARWARS = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/starwars-swg/component/source/",
        file_name="starwars.xml",
    )
    _TOR = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/starwars-swtor/component/target/",
        file_name="swtor.xml",
    )
    _SWG = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/starwars-swg/component/target/",
        file_name="swg.xml",
    )
    _MARVEL = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/marvelcinematicuniverse-marvel/component/target/",
        file_name="marvel.xml",
    )
    _MCU = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/marvelcinematicuniverse-marvel/component/source/",
        file_name="marvelcinematicuniverse.xml",
    )
    _MEMORY_ALPHA = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/memoryalpha-stexpanded/component/source/",
        file_name="memoryalpha.xml",
    )
    _STEXPANDED = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/memoryalpha-stexpanded/component/target/",
        file_name="stexpanded.xml",
    )
    _MEMORY_BETA = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/memoryalpha-memorybeta/component/target/",
        file_name="memorybeta.xml",
    )
    _SW_SWG = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/starwars-swg/component/reference.xml",
        file_name="ref-starwars-swg.xml",
    )
    _SW_TOR = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/starwars-swtor/component/reference.xml",
        file_name="ref-starwars-swtor.xml",
    )
    _MCU_MARVEL = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/marvelcinematicuniverse-marvel/component/reference.xml",
        file_name="ref-marvelcinematicuniverse-marvel.xml",
    )
    _MEMORY_ALPHA_BETA = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/memoryalpha-memorybeta/component/reference.xml",
        file_name="ref-memoryalpha-memorybeta.xml",
    )

    _MEMORY_ALPHA_STEXPANDED = URLWithFileName(
        url="http://oaei.webdatacommons.org/tdrs/testdata/persistent/knowledgegraph/v3/suite/memoryalpha-stexpanded/component/reference.xml",
        file_name="ref-memoryalpha-stexpanded.xml",
    )

    _TASKS = {
        "starwars-swg": OAEITaskFiles(kg1=_STARWARS, kg2=_SWG, ref=_SW_SWG),
        "starwars-swtor": OAEITaskFiles(kg1=_STARWARS, kg2=_TOR, ref=_SW_TOR),
        "marvelcinematicuniverse-marvel": OAEITaskFiles(
            kg1=_MCU, kg2=_MARVEL, ref=_MCU_MARVEL
        ),
        "memoryalpha-memorybeta": OAEITaskFiles(
            kg1=_MEMORY_ALPHA, kg2=_MEMORY_BETA, ref=_MEMORY_ALPHA_BETA
        ),
        "memoryalpha-stexpanded": OAEITaskFiles(
            kg1=_MEMORY_ALPHA, kg2=_STEXPANDED, ref=_MEMORY_ALPHA_STEXPANDED
        ),
    }

    def __init__(self, task: str, data_folder: str = None):
        """Initialize a OAEI Knowledge Graph Track task.

        Parameters
        ----------
        task : str
            Name of the task.
            Has to be one of {starwars-swg,starwars-swtor,marvelcinematicuniverse-marvel,memoryalpha-memorybeta, memoryalpha-stexpanded}
        data_folder : str
            folder where raw files are stored or will be downloaded
        """
        if not task.lower() in self.__class__._TASKS:
            raise ValueError(
                f"Task has to be one of {self.__class__._TASKS}, but got{task}"
            )
        task = task.lower()
        self.task = task
        dl_task = self.__class__._TASKS[self.task]
        super(OAEIKGDataset, self).__init__(
            download_urls=[dl_task.kg1, dl_task.kg2, dl_task.ref],
            data_folder=data_folder,
        )
        self.download()
        self.er_task = self._load()

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"(task={self.task}, data_folder={self.data_folder})"
        )

    def _load_entity_links(self, path: str) -> ClusterHelper:
        print("Parsing ref graph")
        ref = Graph()
        ref.parse(path, format="xml")
        pairs = {}
        for stmt in tqdm(ref, desc="Gathering links"):
            s, p, o = stmt
            if (
                "http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity"
                in str(p)
            ):
                # key is BNode id, value is entity id tuple
                tup = (None, None)
                if str(s) in pairs:
                    tup = pairs[str(s)]
                if "alignmententity1" in str(p):
                    tup = (str(o), tup[1])
                else:
                    tup = (tup[0], str(o))
                pairs[str(s)] = tup
        links = [{t[0], t[1]} for _, t in pairs.items()]
        return ClusterHelper(links)

    def _load(self) -> ERTask:
        dl_task = self.__class__._TASKS[self.task]
        left_name = dl_task.kg1.file_name.replace(".xml", "")
        right_name = dl_task.kg2.file_name.replace(".xml", "")
        kg_left = load_from_rdf(
            os.path.join(self.data_folder, dl_task.kg1.file_name),
            format="xml",
            kg_name=left_name,
        )
        kg_right = load_from_rdf(
            os.path.join(self.data_folder, dl_task.kg2.file_name),
            format="xml",
            kg_name=right_name,
        )
        ref_links = self._load_entity_links(
            os.path.join(self.data_folder, dl_task.ref.file_name)
        )
        return ERTask(kgs=[kg_left, kg_right], clusters=ref_links)
