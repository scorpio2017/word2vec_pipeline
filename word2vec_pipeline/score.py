import itertools
from utils.os_utils import mkdir
import document_scoring as ds
from utils.db_utils import item_iterator


def score_from_config(global_config):

    config = global_config["score"]

    mkdir(config["output_data_directory"])

    #
    # Fill the pipeline with function objects

    mapreduce_functions = []
    for name in config["mapreduce_commands"]:

        obj = getattr(ds, name)

        # Load any kwargs in the config file
        kwargs = {}
        if name in config:
            kwargs = config[name]

        # Add in the embedding configuration options
        kwargs["embedding"] = global_config["embedding"]
        kwargs["score"] = global_config["score"]

        val = name, obj(**kwargs)
        mapreduce_functions.append(val)

    col = global_config['target_column']

    for name, func in mapreduce_functions:
        print("Starting mapreduce {}".format(func.table_name))
        INPUT_ITR = item_iterator(config, text_column=col,
                                  progress_bar=True)

        ITR = itertools.imap(func, INPUT_ITR)
        map(func.reduce, ITR)

        func.save(config)

    #
    # Run the functions that act globally on the data

    for name in config["globaldata_commands"]:
        obj = getattr(ds, name)

        # Load any kwargs in the config file
        kwargs = config
        if name in config:
            kwargs.update(config[name])

        # Add in the embedding configuration options

        func = obj(**kwargs)
        func.set_iterator_function(item_iterator, config)
        func.compute()
        func.save()


if __name__ == "__main__":

    import simple_config
    config = simple_config.load()
    score_from_config(config)
