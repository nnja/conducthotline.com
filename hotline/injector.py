# Copyright 2019 Alethea Katherine Flowers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A really (really) simple dependency injector.

This is mostly just to keep code that requires client libraries & auth
relatively sane.
"""

import functools
import inspect
from typing import Any, Dict, List

_registry: Dict[str, Any] = dict()


def set(name: str, value: Any):
    """Sets a value to be injected.

    value can also be a callable, which will mean that it is treated as a
    factory function. It will be invoked *once* at runtime to create the
    needed value.
    """
    _registry[name] = value


_default_sentinel = object()


def _dot_get(name: str, container: dict):
    parts = name.split(".", 1)

    if name in container:
        return container[name]

    if len(parts) > 1:
        return _dot_get(parts[1], container[parts[0]])
    else:
        return container[parts[0]]


def get(name: str, default=_default_sentinel):
    try:
        value = _dot_get(name, _registry)

        if callable(value):
            value = value()
            # Update the value so we only call factories once.
            _registry[name] = value

        return value

    except KeyError:
        if default is not _default_sentinel:
            return default

        raise KeyError(f"{name} has not been provided.")


def _modify_function_signature(func, injected_items: List[str]):
    """Modifies a function sigature to turn any injected items into optional
    keyword args. This makes injection play nicely with mock's autospeccing.
    """
    signature = inspect.signature(func)

    regular_params = [
        param
        for param in signature.parameters.values()
        if param.name not in injected_items
    ]

    new_params = [
        param.replace(kind=inspect.Parameter.KEYWORD_ONLY, default=None)
        for param in signature.parameters.values()
        if param.name in injected_items
    ]

    signature = signature.replace(parameters=regular_params + new_params)

    func.__signature__ = signature


def needs(*things):
    """An injector that injects the requested dependences into a function's
    arguments.

    If the dependency has "."s in the name, only the last segment will be used,
    and "-" will be replaced with "_".
    """

    things_parameter_names = {
        requirement.rsplit(".", 1)[-1].replace("-", "_"): requirement
        for requirement in things
    }

    def decorator(f):
        @functools.wraps(f)
        def invocation(*args, **kwargs):
            for parameter, requirement in things_parameter_names.items():
                if parameter not in kwargs:
                    kwargs[parameter] = get(requirement)
            return f(*args, **kwargs)

        _modify_function_signature(invocation, list(things_parameter_names.keys()))
        return invocation

    return decorator


# Avoid shadowing below
_needs = needs


def provides(name=None, needs: List[str] = None):
    """A shortcut for defining a factory function that also needs dependencies
    itself."""
    if not needs:
        needs = []

    def decorator(f):
        decorated = _needs(*needs)(f)
        set(name or f.__name__, decorated)
        return f

    return decorator


def reset():
    _registry.clear()
