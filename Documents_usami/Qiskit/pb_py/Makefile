PROTO_DIR = ../proto
PROTO_FILES = $(PROTO_DIR)/qc_simulator.proto
PROTO_GEN_FILES = qc_simulator_pb2.py qc_simulator_pb2.pyi qc_simulator_pb2_grpc.py

all: $(PROTO_GEN_FILES)

$(PROTO_GEN_FILES): $(PROTO_FILES)
	python -m grpc_tools.protoc -I $(PROTO_DIR) --python_out=. --pyi_out=. --grpc_python_out=. $<

clean:
	rm $(PROTO_GEN_FILES)

.PHONY: all clean
