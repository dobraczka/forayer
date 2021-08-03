from typing import Dict, Tuple


def read_attr_triples(path: str) -> Dict[str, Dict[str, str]]:
    ent_attr_dict = dict()
    with open(path, "r") as in_file:
        for line in in_file:
            e_id, prop, value = line.split("\t")
            if e_id not in ent_attr_dict:
                ent_attr_dict[e_id] = dict()
            ent_attr_dict[e_id][prop] = value
    return ent_attr_dict


def read_rel_triples(
    path: str,
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    rel_left_to_right_dict = dict()
    rel_right_to_left_dict = dict()
    with open(path, "r") as in_file:
        for line in in_file:
            left_id, rel, right_id = line.split("\t")
            if left_id not in rel_left_to_right_dict:
                rel_left_to_right_dict[left_id] = dict()
            if right_id not in rel_right_to_left_dict:
                rel_right_to_left_dict[right_id] = dict()
            rel_left_to_right_dict[left_id][right_id] = rel
            rel_right_to_left_dict[right_id][left_id] = rel
    return rel_left_to_right_dict, rel_right_to_left_dict


def read_links(inpath, fold):
    fold_path = os.path.join(inpath, "721_5fold", str(fold))
    return (
        read_tsv(os.path.join(fold_path, "train_links")),
        read_tsv(os.path.join(fold_path, "test_links")),
        read_tsv(os.path.join(fold_path, "valid_links")),
    )


def from_openea(path: str):
    pass
