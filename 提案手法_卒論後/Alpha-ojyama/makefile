CXX = g++

ifeq ($(PROF), true)
CXXPROF += -pg -no-pie
else
CXXPROF += -s
endif

ifeq ($(BUILD), debug)
CXXFLAGS += -fdiagnostics-color=always -DUNICODE -std=c++20 -Wall -Og -pg -no-pie
else
CXXFLAGS += -DUNICODE -DNDEBUG -std=c++20 -O3 -msse4 -mbmi2 -flto $(CXXPROF) -march=native
endif

ifeq ($(PEXT), true)
CXXFLAGS += -DPEXT
endif

STATIC_LIB = -lsetupapi -lhid -luser32 -lgdi32 -lgdiplus -lShlwapi -ldwmapi -lstdc++fs -static -static-libgcc

SRC_AI = core/*.cpp ai/search/beam/*.cpp ai/search/dfs/*.cpp ai/search/*.cpp ai/*.cpp

SDL_DIR = D:/c++/lib/sdl/x86_64-w64-mingw32
SDL_INC = -I$(SDL_DIR)/include/SDL2
SDL_LIB = -L$(SDL_DIR)/lib -lmingw32 -lSDL2main -lSDL2 -mwindows -Wl,--dynamicbase -Wl,--nxcompat -Wl,--high-entropy-va -lm -ldinput8 -ldxguid -ldxerr8 -luser32 -lgdi32 -lwinmm -limm32 -lole32 -loleaut32 -lshell32 -lsetupapi -lversion -luuid

GUI_DIR = D:/c++/lib/imgui
GUI_INC = -I$(GUI_DIR) -I$(GUI_DIR)/backends
GUI_SRC = $(GUI_DIR)/*.cpp $(GUI_DIR)/backends/imgui_impl_sdl2.cpp $(GUI_DIR)/backends/imgui_impl_sdlrenderer2.cpp

PPC_NAME = ppc
PPC_SRC = $(SRC_AI)
PPC_LIB = $(STATIC_LIB)

ifeq ($(GUI), true)
CXXFLAGS += -DGUI
PPC_NAME = ppc_gui
PPC_SRC += $(SDL_INC) $(GUI_INC) $(GUI_SRC)
PPC_LIB += $(SDL_LIB)
endif

ifeq ($(CHEAT), true)
CXXFLAGS += -DCHEAT
endif

.PHONY: all puyop ppc test clean makedir puyop_alphazero

all: puyop ppc

ppc: makedir
	@$(CXX) $(CXXFLAGS) $(PPC_SRC) ppc/*.cpp $(PPC_LIB) -o bin/ppc/$(PPC_NAME).exe

puyop: makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) puyop/main.cpp -o bin/puyop/puyop.exe

puyop_alphazero: makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) puyop/main_alphazero.cpp -o bin/puyop/puyop_alphazero.exe

tuner: makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) tuner/*.cpp -o bin/tuner/tuner.exe

test: makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) test/*.cpp -o bin/test/test.exe

clean: makedir
	@rm -rf bin
	@make makedir

# データ収集用
puyop_collect:  makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) puyop/main_collect.cpp -o bin/puyop/puyop_collect.exe

puyop_record:  $(OBJ_PUYOP_RECORD)
	$(CXX) $(CXXFLAGS) -o bin/puyop/$@ $^ $(LDFLAGS)

OBJ_PUYOP_RECORD = \
	obj/puyop/main_record.o \
	obj/core/field.o \
	obj/core/ctrl.o \
	obj/core/chain.o \
	obj/core/player.o \
	obj/core/pattern.o \
	obj/core/AI.o

obj/puyop/main_record.o: puyop/main_record.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# C++ Simulator for Python (same pattern as puyop)
puyop_simulator: makedir
	@$(CXX) $(CXXFLAGS) $(SRC_AI) puyop/main_simulator.cpp -o bin/puyop/puyop_simulator.exe

makedir:
	@mkdir -p bin
	@mkdir -p bin/puyop
	@mkdir -p bin/ppc
	@mkdir -p bin/test
	@mkdir -p bin/tuner/data

.DEFAULT_GOAL := puyop