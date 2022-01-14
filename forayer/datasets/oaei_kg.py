"""OAEI knowledge graph track dataset class."""

from collections import namedtuple
from typing import Dict, Optional, Tuple

import pystow
from forayer.datasets.base_dataset import ForayerDataset
from forayer.input_output.from_to_rdf import from_rdflib
from forayer.knowledge_graph import ClusterHelper, ERTask
from pystow import ensure_rdf
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


class OAEIKGDataset(ForayerDataset):
    """The  OAEI (Ontology Alignment Evaluation Initiative) Knowledge Graph Track tasks contain graphs created from fandom wikis.

    Five integration tasks are available:
        - starwars-swg
        - starwars-swtor
        - marvelcinematicuniverse-marvel
        - memoryalpha-memorybeta
        - memoryalpha-stexpanded

    More information can be found at the `website <http://oaei.ontologymatching.org/2019/knowledgegraph/index.html>`_.
    """

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

    def __init__(self, task: str, force: bool = False):
        """Initialize a OAEI Knowledge Graph Track task.

        Parameters
        ----------
        task : str
            Name of the task.
            Has to be one of {starwars-swg,starwars-swtor,marvelcinematicuniverse-marvel,memoryalpha-memorybeta, memoryalpha-stexpanded}
        force : bool
            if true ignores cache
        """
        if not task.lower() in self.__class__._TASKS:
            raise ValueError(
                f"Task has to be one of {self.__class__._TASKS}, but got{task}"
            )
        task = task.lower()
        self.task = task
        super().__init__(
            name=self.task,
            cache_path=pystow.join("forayer", "cache", name=f"OAEI_KG_{task}.pkl"),
            force=force,
        )

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"(task={self.task}, data_folder={self.data_folder})"
        )

    def _load_entity_links(self, ref: Graph) -> ClusterHelper:
        print("Parsing ref graph")
        pairs: Dict[str, Tuple[str, str]] = {}
        for stmt in tqdm(ref, desc="Gathering links"):
            s, p, o = stmt
            if (
                "http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity"
                in str(p)
            ):
                # key is BNode id, value is entity id tuple
                tup: Tuple[str, str] = ("", "")
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
        dl_task: OAEITaskFiles = self.__class__._TASKS[self.task]
        left_name = dl_task.kg1.file_name.replace(".xml", "")
        right_name = dl_task.kg2.file_name.replace(".xml", "")
        kg_left_rdf = ensure_rdf(
            "forayer",
            "OAEI_KG",
            self.task,
            name=dl_task.kg1.file_name,
            url=dl_task.kg1.url,
            parse_kwargs={"format": "xml"},
        )
        kg_left = from_rdflib(kg_left_rdf, kg_name=left_name)
        kg_right_rdf = ensure_rdf(
            "forayer",
            "OAEI_KG",
            self.task,
            name=dl_task.kg2.file_name,
            url=dl_task.kg2.url,
            parse_kwargs={"format": "xml"},
        )
        kg_right = from_rdflib(kg_right_rdf, kg_name=right_name)
        kg_ref = ensure_rdf(
            "forayer",
            "OAEI_KG",
            self.task,
            name=dl_task.ref.file_name,
            url=dl_task.ref.url,
            parse_kwargs={"format": "xml"},
        )
        ref_links = self._load_entity_links(kg_ref)
        return ERTask(kgs=[kg_left, kg_right], clusters=ref_links)
