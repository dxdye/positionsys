# positionsys
Position system is API for trading bots and gets data

## install 

```
git switch main && git pull
```
and then..
```
pixi install 
```

## testing 
execute all tests (tbd.)
```
pixi run test
```
or 
```
pixi run test::$CASE$
```

## generate documentation

to generate the doc out of this code, use the following commands: 

to run it as web app on localhost: 
```
pixi run docs
```

to save it locally in a folder `./docs`: 
```
pixi run docs:saved
```

the docs should be hosted via GitHub Pages on: 
https://dxdye.github.io/positionsys/





## format & VsCode

to format the project use 

```
pixi run fmt
```

or for single file format on save, 
just install the default ruff extension for VsCode.