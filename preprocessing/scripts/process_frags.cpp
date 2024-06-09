#include <algorithm>
#include <fstream>
#include <iostream>
#include <stdlib.h>
#include <string>
#include <vector>


/*****
// HELPER FUNCTIONS
*****/
bool is_valid_chr(std::string chr_name, std::vector<std::string> allowed_chrs) {
	return std::find(allowed_chrs.begin(), allowed_chrs.end(), chr_name) != allowed_chrs.end();
}

std::vector<std::string> load_list(std::string file_loc) {
	std::vector<std::string> items;
	std::ifstream listfile(file_loc);
	std::string x;
	while (listfile >> x) {
		items.push_back(x);
	}
	listfile.close();
	return items;
}

std::string revcomp(std::string sequence) {
	std::string revseq = "";
	for (int i = 0; i < sequence.length(); i++) {
		char current_base = sequence.at(sequence.length() - 1 - i);
		if (current_base == 'A') {
			revseq += 'T';
		} else if (current_base == 'T') {
			revseq += 'A';
		} else if (current_base == 'C') {
			revseq += 'G';
		} else if (current_base == 'G') {
			revseq += 'C';
		} else {
			throw std::invalid_argument("INVALID BASE PAIR: " + current_base);
		}
	}
	return revseq;
}


/******
// DNATree DATA STRUCTURE
*****/
struct Node {
	Node* A = NULL;
	Node* T = NULL;
	Node* C = NULL;
	Node* G = NULL;
	std::string info = "";
};

class DNATree {
	public:
		Node* root;
		std::vector<Node*> allNodes;
		DNATree ();
		~DNATree ();
		void addSeq (std::string, std::string);
		bool hasSeq (std::string);
		std::string getSeq (std::string);
};

DNATree::DNATree () {
	root = new Node;
	allNodes.push_back(root);
};

DNATree::~DNATree() {
	for (int i = 0; i < allNodes.size(); i++) {
		delete allNodes[i];
	}
};

void DNATree::addSeq (std::string sequence, std::string node_info) {
	Node* current_node = root;
	for (int i = 0; i < sequence.length(); i++) {
		char current_base = sequence.at(i);
		if (current_base == 'A') {
			if (current_node->A == NULL) {
				Node* new_node = new Node;
				current_node->A = new_node;
				allNodes.push_back(new_node);
				current_node = new_node;
			} else {
				current_node = current_node->A;
			}
		} else if (current_base == 'T') {
			if (current_node->T == NULL) {
				Node* new_node = new Node;
				current_node->T = new_node;
				allNodes.push_back(new_node);
				current_node = new_node;
			} else {
				current_node = current_node->T;
			}		
		} else if (current_base == 'C') {
			if (current_node->C == NULL) {
				Node* new_node = new Node;
				current_node->C = new_node;
				allNodes.push_back(new_node);
				current_node = new_node;
			} else {
				current_node = current_node->C;
			}
		} else if (current_base == 'G') {
			if (current_node->G == NULL) {
				Node* new_node = new Node;
				current_node->G = new_node;
				allNodes.push_back(new_node);
				current_node = new_node;
			} else {
				current_node = current_node->G;
			}
		} else {
			throw std::invalid_argument("INVALID BASE PAIR: " + current_base);
		}
		if (i == sequence.length()-1) {
			current_node->info = node_info;
		}
	}
};

bool DNATree::hasSeq (std::string sequence) {
	Node* current_node = root;
	for (int i = 0; i < sequence.length(); i++) {
		char current_base = sequence.at(i);
		if (current_base == 'A') {
			if (current_node->A == NULL) {
				return false;
			} else {
				current_node = current_node->A;
			}
		} else if (current_base == 'T') {
			if (current_node->T == NULL) {
				return false;
			} else {
				current_node = current_node->T;
			}
		} else if (current_base == 'C') {
			if (current_node->C == NULL) {
				return false;
			} else {
				current_node = current_node->C;
			}
		} else if (current_base == 'G') {
			if (current_node->G == NULL) {
				return false;
			} else {
				current_node = current_node->G;
			}
		} else {
			throw std::invalid_argument("INVALID BASE PAIR: " + current_base);
		}
	}
	return true;
};

std::string DNATree::getSeq (std::string sequence) {
	Node* current_node = root;
	for (int i = 0; i < sequence.length(); i++) {
		char current_base = sequence.at(i);
		if (current_base == 'A') {
			if (current_node->A == NULL) {
				return "seq not found";
			} else {
				current_node = current_node->A;
			}
		} else if (current_base == 'T') {
			if (current_node->T == NULL) {
				return "seq not found";
			} else {
				current_node = current_node->T;
			}
		} else if (current_base == 'C') {
			if (current_node->C == NULL) {
				return "seq not found";
			} else {
				current_node = current_node->C;
			}
		} else if (current_base == 'G') {
			if (current_node->G == NULL) {
				return "seq not found";
			} else {
				current_node = current_node->G;
			}
		} else {
			throw std::invalid_argument("INVALID BASE PAIR: " + current_base);
		}
	}
	return current_node->info;
};

/******
// MAIN CODE
*****/
int main(int argc, char** argv) {
	// PARSE CLI ARGUMENT
	std::string barcode_name = argv[1];
	std::string sample_celltype = barcode_name.substr(0, barcode_name.length()-4);
	std::string sample = sample_celltype.substr(0, sample_celltype.find("-"));
	std::string celltype = sample_celltype.substr(sample_celltype.find("-")+1);
	// std::cout << sample << " " << celltype << std::endl;

	// SET UP FILE LOCs
	std::string barcodes_dir = argv[2]; //
	std::string barcode_file_in = barcodes_dir + barcode_name;

	std::string frags_dir = argv[3]; //
	std::string frags_in = frags_dir + "/" + sample + ".tsv";
	std::string base_dir = argv[4]; //
	std::string frags_out = base_dir + "fragments/" + celltype + "-" + sample + ".tsv";
	std::string pseudorep1_out = base_dir + "pseudorep1/" + celltype + "-" + sample + ".tsv";
	std::string pseudorep2_out = base_dir + "pseudorep2/" + celltype + "-" + sample + ".tsv";
	std::string pseudorepT_out = base_dir + "pseudorepT/" + celltype + "-" + sample + ".tsv";
	// std::cout << barcode_file_in << "\n" + frags_in << "\n" << frags_out << "\n" << pseudorep1_out << "\n" << pseudorep2_out << "\n" << pseudorepT_out << std::endl;

	// READ IN ALLOWED BARCODES + SET UP DNATree
	std::vector<std::string> allowed_barcodes = load_list(barcode_file_in);
	DNATree mytree;
	for (int i = 0; i < allowed_barcodes.size(); i++) {
		mytree.addSeq(allowed_barcodes[i], celltype);
	}

	// SET UP ALL OUT WRITERS
	std::ofstream f_out_writer(frags_out);
	std::ofstream p1_out_writer(pseudorep1_out);
	std::ofstream p2_out_writer(pseudorep2_out);
	std::ofstream pT_out_writer(pseudorepT_out);

	// SET UP READ PARAMETERS
	std::string chr, barcode, reads;
	int start, end;
	long kept_frags = 0;
	std::ifstream infile(frags_in);
	std::vector<std::string> allowed_chrs = {"chr1", "chr10", "chr11", "chr12", "chr13", "chr14", "chr15", "chr16", "chr17", "chr18", "chr19", "chr2", "chr20", "chr21", "chr22", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9", "chrX", "chrY"};

	// BEGIN PARSING FILE
	while (infile >> chr >> start >> end >> barcode >> reads) {
		barcode = barcode.substr(0, 16);
		if (mytree.hasSeq(barcode) && is_valid_chr(chr, allowed_chrs)) {
			std::string barcode_out = sample + "#" + barcode;
			kept_frags++;
			// WRITE TO FRAGS OUT
			f_out_writer << chr << "\t" << start << "\t" << end << "\t" << barcode_out << "\t" << reads << "\n";
			// WRITE INSERTIONS TO pT
			pT_out_writer << chr << "\t" << start << "\t" << start+1 << "\t" << barcode_out << "\t" << reads << "\n";
			pT_out_writer << chr << "\t" << end-1 << "\t" << end << "\t" << barcode_out << "\t" << reads << "\n";
			// WRITE INSERTIONS TO p1/p2
			if (rand() % 2 == 0) {
				p1_out_writer << chr << "\t" << start << "\t" << start+1 << "\t" << barcode_out << "\t" << reads << "\n";
			} else {
				p2_out_writer << chr << "\t" << start << "\t" << start+1 << "\t" << barcode_out << "\t" << reads << "\n";
			}
			// WRITE END INSERTION TO r1/r2
			if (rand() % 2 == 0) {
				p1_out_writer << chr << "\t" << end-1 << "\t" << end << "\t" << barcode_out << "\t" << reads << "\n";
			} else {
				p2_out_writer << chr << "\t" << end-1 << "\t" << end << "\t" << barcode_out << "\t" << reads << "\n";
			}
		}
	}

	// CLOSE IO STREAMS
	infile.close();
	f_out_writer.close();
	p1_out_writer.close();
	p2_out_writer.close();
	pT_out_writer.close();

	// PRINT RESULTS
	std::cout << sample << " " << celltype << ": " << allowed_barcodes.size() << " barcodes, " << kept_frags << " frags" << std::endl;

	return 0;
}
