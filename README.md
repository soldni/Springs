
# Springs

![Logo of Springs. Generated using DALL·E mini.](https://github.com/soldni/Springs/raw/main/static/logo.png)

A set of utilities to turn [OmegaConf][1] into a fully fledge configuration utils.
Just like the springs inside an Omega watch, they help you move with your experiments.

Springs overlaps in functionality with [Hydra][2], but without all the unnecessary boilerplate.

The current logo for Springs was generated using [DALL·E 2][5].

## Philosophy

OmegaConf supports creating configurations in all sorts of manners, but we believe that there are benefits into defining configuration from structured objects, namely dataclass.
Springs is built around that notion: write one or more dataclass to compose a configuration (with appropriate defaults), then parse the remainder of options or missing values from command line/a yaml file.

Let's look at an example. Imagine we are building a configuration for a machine learning (ML) experiment, and we want to provide information about model and data to use.
We start by writing the following structure configuration

```python
import springs as sp

@sp.dataclass                   # alias to dataclasses.dataclass
class DataConfig:
    path: str = sp.MISSING      # alias to dataclasses.MISSING
    split: str = 'train'

@sp.dataclass
class ModelConfig:
    name: str = sp.MISSING
    num_labels: int = 2

@sp.dataclass
class ExperimentConfig:
    batch_size: int = 16
    seed: int = 42

@sp.dataclass
class Config:                   # this is our overall config
    data: DataConfig = DataConfig()
    model: ModelConfig = ModelConfig()
    exp: ExperimentConfig = ExperimentConfig()
```

Note how, in matching with OmegaConf syntax, we use `MISSING` to indicate any value that has no default and should be provided at runtime.

If we want to use this configuration with a function that actually runs this experiment, we can use `sp.cli` as follows:

```python
@sp.cli(Config)
def main(config: Config)
    print(config)           # this will print the configuration like a dict
    config.exp.seed         # you can use dot notation to access attributes...
    config['exp']['seed']   # ...or treat it like a dictionary!


if __name__ == '__main__':
    main()

```

Notice how, in the configuration `Config` above, some parameters are missing.
We can specify them from command line...

```bash
python main.py data.path=/path/to/data model.name=bert-base-uncased
```

...or from one or more YAML config files (if multiple, the latter ones override the former ones).


```YAML
data:
    path: /path/to/data

model:
    name: bert-base-uncased

# you can override any part of the config via YAML or CLI
# CLI takes precedence over YAML.
exp:
    seed: 1337

```

To run with from YAML, do:

```bash
python main.py -c config.yaml
```

Easy, right?


### Fine, We Do Support Support Unstructured Configurations

You are not required to used a structured config with Springs.
To use our CLI with a bunch of yaml files and/or command line arguments, simply decorate your main function with no arguments.

```python
@sp.cli()
def main(config)
    # do stuff
    ...
```


### Initializing Object from Configurations

Sometimes a configuration contains all the necessary information to
instantiate an object from it.
Springs supports this use case, and it is as easy as providing a `_target_` node in a configuration:

```python
@sp.dataclass
class ModelConfig:
    _target_: str = \
        'transformers.AutoModelForSequenceClassification.from_pretrained'
    pretrained_model_name_or_path: str = 'bert-base-uncased'
    num_classes: int = 2
```

In your experiment code, run:

```python
def run_model(model_config: ModelConfig):
    ...
    model = sp.init.now(model_config, ModelConfig)
```

**Note:** Previous versions of Springs supported specifying the return type,
but now it is actively encouraged. Running `sp.init.now(model_config)` will
now raise a warning if the type is not provided. To prevent this warning,
use `sp.toggle_warnings(False)` before calling `sp.init.now`/ `sp.init.later`.

### `init.now` vs `init.later`

`init.now` is used to immediately initialize a class or run a method.
But what if the function you are not ready to run the `_target_` you want to initialize?
This is common for example if you receive a configuration in the init method of a class, but you don't have all parameters to run it until later in the object lifetime. In that case, you might want to use `init.later`.
Example:

```python
config = sp.from_dict({'_target_': 'str.lower'})
fn = sp.init.later(config, Callable[..., str])

... # much computation occurs

fn('THIS TO LOWERCASE')     # returns `this to lowercase`
```

Note that, for convenience `sp.init.now` is aliased to `sp.init`.

### Path as `_target_`

If, for some reason, cannot specify the path to a class as a string, you can use `sp.Target.to_string` to resolve a function, class, or method to its path:

```python
import transformers

@sp.dataclass
class ModelConfig:
    _target_: str = sp.Target.to_string(transformers.
                                        AutoModelForSequenceClassification.
                                        from_pretrained)
    pretrained_model_name_or_path: str = 'bert-base-uncased'
    num_classes: int = 2
```

### Static and Dynamic Type Checking

Springs supports both static and dynamic (at runtime) type checking when initializing objects.
To enable it, pass the expected return type when initializing an object:

```python
@sp.cli(TokenizerConfig)
def main(config: TokenizerConfig):
    tokenizer = sp.init(config, PreTrainedTokenizerBase)
    print(tokenizer)
```

This will raise an error when the tokenizer is not a subclass of `PreTrainedTokenizerBase`. Further, if you use a static type checker in your workflow (e.g., [Pylance][3] in [Visual Studio Code][4]), `springs.init` will also annotate its return type accordingly.


### Flexible Configurations

Sometimes a configuration has some default parameters, but others are optional and depend on other factors, such as the `_target_` class.  In these cases, it is convenient to set up a flexible dataclass, using `make_flexy` after the `dataclass` decorator.

```python
@sp.make_flexy
@sp.dataclass
class MetricConfig:
    _target_: str = sp.MISSING
    average: str = 'macro'

config = sp.from_flexyclass(MetricConfig)
overrides = {
    '_target_': 'torchmetrics.F1Score',    # we override the _target_
    'num_classes': 2    # this attribute does not exist in the structured config
}

config = sp.merge(config, sp.from_dict(overrides))
print(config)
# this will print the following:
# {'_target_': 'torchmetrics.F1Score', 'average': 'macro', 'num_classes': 2}
```

**Note:** In previous version of Springs, the canonical way to create a flexible class was to decorate a class with `@sp.flexyclass`. This method is still there, but it is not encouraged since it creates issues with `mypy` (and potentially other type checkers). Please consider switching to `dataclass` followed by `make_flexy`. To prevent a warning being raised for this, use
`sp.toggle_warnings(False)` before calling `sp.flexyclass`.

### Resolvers

Guide coming soon!

## Tips and Tricks

This section includes a bunch of tips and tricks for working with OmegaConf and YAML.

### Tip 1: Repeating nodes in YAML input

In setting up YAML configuration files for ML experiments, it is common to
have almost-repeated sections.
In these cases, you can take advantage of YAML's built in variable mechanism and dictionary merging to remove duplicated imports:

```yaml
# &tc assigns an alias to this node
train_config: &tc
  path: /path/to/data
  src_field: full_text
  tgt_field: summary
  split_name: train

test_config:
  # << operator indicates merging,
  # *tc is a reference to the alias above
  << : *tc
  split_name: test
```

This will resolve to:

```yaml
train_config:
  path: /path/to/data
  split_name: train
  src_field: full_text
  tgt_field: summary

test_config:
  path: /path/to/data
  split_name: test
  src_field: full_text
  tgt_field: summary
```


[1]: https://omegaconf.readthedocs.io/
[2]: https://hydra.cc/
[3]: https://devblogs.microsoft.com/python/announcing-pylance-fast-feature-rich-language-support-for-python-in-visual-studio-code/
[4]: https://code.visualstudio.com
[5]: https://openai.com/dall-e-2/
